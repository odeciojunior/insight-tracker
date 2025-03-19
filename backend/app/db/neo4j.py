"""
Neo4j connection module for the Insight Tracker application.

Provides asynchronous access to Neo4j for graph operations and relationships management.
"""

import logging
import asyncio
import uuid
from typing import Any, Dict, List, Optional, Union, Tuple, Callable, TypeVar
from neo4j import GraphDatabase, AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, ClientError, TransactionError
from neo4j.data import Record

# Configure logging
logger = logging.getLogger(__name__)

# Type variables for record conversion
T = TypeVar('T')

class Neo4jClient:
    """
    Asynchronous Neo4j client with retry mechanism and utility methods.
    
    This class provides a wrapper around AsyncGraphDatabase for asynchronous Neo4j operations
    with built-in retry logic for resilience and utility functions for common graph operations.
    """
    
    def __init__(
        self,
        uri: str,
        username: str,
        password: str,
        database: str = "neo4j",
        max_retry_attempts: int = 3,
        retry_delay: float = 0.5,
        connection_timeout: int = 30,
        max_connection_lifetime: int = 3600,
        max_connection_pool_size: int = 50
    ):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j server URI
            username: Neo4j username
            password: Neo4j password
            database: Default database name
            max_retry_attempts: Maximum number of retry attempts on failed operations
            retry_delay: Delay between retry attempts in seconds
            connection_timeout: Connection timeout in seconds
            max_connection_lifetime: Maximum lifetime of a connection in seconds
            max_connection_pool_size: Maximum size of the connection pool
        """
        self._uri = uri
        self._username = username
        self._password = password
        self._database = database
        self._max_retry_attempts = max_retry_attempts
        self._retry_delay = retry_delay
        self._connection_timeout = connection_timeout
        self._max_connection_lifetime = max_connection_lifetime
        self._max_connection_pool_size = max_connection_pool_size
        
        self._driver: Optional[AsyncDriver] = None
    
    async def connect(self) -> None:
        """
        Establish connection to Neo4j with retry mechanism.
        """
        for attempt in range(1, self._max_retry_attempts + 1):
            try:
                logger.info(f"Connecting to Neo4j (attempt {attempt}/{self._max_retry_attempts})...")
                self._driver = AsyncGraphDatabase.driver(
                    self._uri,
                    auth=(self._username, self._password),
                    connection_timeout=self._connection_timeout,
                    max_connection_lifetime=self._max_connection_lifetime,
                    max_connection_pool_size=self._max_connection_pool_size
                )
                
                # Verify connection by running simple query
                await self.run_query("RETURN 1 AS result")
                
                logger.info("Successfully connected to Neo4j")
                return
                
            except (ServiceUnavailable, ClientError) as e:
                logger.error(f"Failed to connect to Neo4j (attempt {attempt}/{self._max_retry_attempts}): {str(e)}")
                
                if attempt < self._max_retry_attempts:
                    wait_time = self._retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    logger.info(f"Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.critical("Could not establish connection to Neo4j after multiple attempts")
                    raise
    
    async def close(self) -> None:
        """
        Close Neo4j connection.
        """
        if self._driver:
            logger.info("Closing Neo4j connection...")
            await self._driver.close()
            self._driver = None
            logger.info("Neo4j connection closed successfully")
    
    async def check_health(self) -> bool:
        """
        Check if the Neo4j connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        if not self._driver:
            logger.warning("Health check failed: No Neo4j driver available")
            return False
        
        try:
            # Try to execute a simple query to check the connection
            result = await self.run_query("RETURN 1 AS result")
            if result and len(result) == 1 and result[0].get('result') == 1:
                logger.debug("Neo4j health check: Connection is healthy")
                return True
            return False
        except Exception as e:
            logger.error(f"Neo4j health check failed: {str(e)}")
            return False
    
    async def _execute_with_retry(self, operation, *args, **kwargs) -> Any:
        """
        Execute a Neo4j operation with retry logic.
        
        Args:
            operation: Async function to execute
            *args: Arguments to pass to the operation
            **kwargs: Keyword arguments to pass to the operation
            
        Returns:
            Any: The result of the operation
        """
        if not self._driver:
            raise ConnectionError("Neo4j client is not connected")
            
        for attempt in range(1, self._max_retry_attempts + 1):
            try:
                return await operation(*args, **kwargs)
            except (ServiceUnavailable, TransactionError) as e:
                logger.warning(f"Neo4j operation failed (attempt {attempt}/{self._max_retry_attempts}): {str(e)}")
                
                if attempt < self._max_retry_attempts:
                    wait_time = self._retry_delay * (2 ** (attempt - 1))
                    logger.info(f"Retrying operation in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("Neo4j operation failed after maximum retry attempts")
                    raise
    
    async def run_query(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Run a Cypher query and return the results.
        
        Args:
            query: Cypher query
            parameters: Query parameters
            database: Database name (defaults to the one specified in constructor)
            
        Returns:
            List[Dict[str, Any]]: List of records as dictionaries
        """
        if not parameters:
            parameters = {}
            
        if not database:
            database = self._database
            
        async def execute_query():
            async with self._driver.session(database=database) as session:
                result = await session.run(query, parameters)
                return [record.data() for record in await result.fetch_all()]
                
        return await self._execute_with_retry(execute_query)
    
    async def run_query_single(
        self, 
        query: str, 
        parameters: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Run a Cypher query and return a single record.
        
        Args:
            query: Cypher query
            parameters: Query parameters
            database: Database name (defaults to the one specified in constructor)
            
        Returns:
            Optional[Dict[str, Any]]: Single record as dictionary or None
        """
        result = await self.run_query(query, parameters, database)
        return result[0] if result else None
    
    async def transaction(self, database: Optional[str] = None) -> 'Neo4jTransaction':
        """
        Create a transaction context manager.
        
        Args:
            database: Database name (defaults to the one specified in constructor)
            
        Returns:
            Neo4jTransaction: Transaction context manager
        """
        if not database:
            database = self._database
            
        return Neo4jTransaction(self._driver, database, self._max_retry_attempts, self._retry_delay)
    
    # Node Operations
    
    async def create_node(
        self,
        label: str,
        properties: Dict[str, Any],
        unique_constraints: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a node in the graph.
        
        Args:
            label: Node label
            properties: Node properties
            unique_constraints: Properties to enforce uniqueness on
            database: Database name
            
        Returns:
            Dict[str, Any]: Created node properties including internal ID
        """
        if unique_constraints:
            # Build MERGE query with unique constraints
            constraint_parts = []
            for key, value in unique_constraints.items():
                properties.setdefault(key, value)
                constraint_parts.append(f"n.{key} = ${key}")
                
            constraint_str = " AND ".join(constraint_parts)
            query = f"""
            MERGE (n:{label} {{{constraint_str}}})
            SET n += $properties
            RETURN n
            """
            parameters = {**unique_constraints, "properties": {k: v for k, v in properties.items() if k not in unique_constraints}}
        else:
            # Simple CREATE query
            query = f"""
            CREATE (n:{label} $properties)
            RETURN n
            """
            parameters = {"properties": properties}
            
        result = await self.run_query_single(query, parameters, database)
        return result.get('n') if result else None
    
    async def get_node(
        self,
        label: str,
        properties: Dict[str, Any],
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get a node from the graph.
        
        Args:
            label: Node label
            properties: Properties to match
            database: Database name
            
        Returns:
            Optional[Dict[str, Any]]: Node properties or None if not found
        """
        # Build match conditions
        conditions = []
        for key, value in properties.items():
            conditions.append(f"n.{key} = ${key}")
            
        condition_str = " AND ".join(conditions)
        
        query = f"""
        MATCH (n:{label})
        WHERE {condition_str}
        RETURN n
        """
        
        result = await self.run_query_single(query, properties, database)
        return result.get('n') if result else None
    
    async def update_node(
        self,
        label: str,
        match_properties: Dict[str, Any],
        update_properties: Dict[str, Any],
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Update a node in the graph.
        
        Args:
            label: Node label
            match_properties: Properties to match
            update_properties: Properties to update
            database: Database name
            
        Returns:
            Optional[Dict[str, Any]]: Updated node properties or None if not found
        """
        # Build match conditions
        conditions = []
        for key, value in match_properties.items():
            conditions.append(f"n.{key} = ${key}")
            
        condition_str = " AND ".join(conditions)
        
        query = f"""
        MATCH (n:{label})
        WHERE {condition_str}
        SET n += $update
        RETURN n
        """
        
        parameters = {**match_properties, "update": update_properties}
        
        result = await self.run_query_single(query, parameters, database)
        return result.get('n') if result else None
    
    async def delete_node(
        self,
        label: str,
        properties: Dict[str, Any],
        detach: bool = True,
        database: Optional[str] = None
    ) -> bool:
        """
        Delete a node from the graph.
        
        Args:
            label: Node label
            properties: Properties to match
            detach: Whether to detach (delete) relationships first
            database: Database name
            
        Returns:
            bool: True if node was deleted, False otherwise
        """
        # Build match conditions
        conditions = []
        for key, value in properties.items():
            conditions.append(f"n.{key} = ${key}")
            
        condition_str = " AND ".join(conditions)
        detach_str = "DETACH" if detach else ""
        
        query = f"""
        MATCH (n:{label})
        WHERE {condition_str}
        {detach_str} DELETE n
        RETURN count(n) AS deleted
        """
        
        result = await self.run_query_single(query, properties, database)
        return result.get('deleted', 0) > 0 if result else False
    
    # Relationship Operations
    
    async def create_relationship(
        self,
        from_label: str,
        from_properties: Dict[str, Any],
        to_label: str,
        to_properties: Dict[str, Any],
        relationship_type: str,
        relationship_properties: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Create a relationship between two nodes.
        
        Args:
            from_label: Source node label
            from_properties: Source node properties to match
            to_label: Target node label
            to_properties: Target node properties to match
            relationship_type: Type of relationship
            relationship_properties: Properties for the relationship
            database: Database name
            
        Returns:
            Optional[Dict[str, Any]]: Created relationship properties or None
        """
        if relationship_properties is None:
            relationship_properties = {}
            
        # Build match conditions for source and target nodes
        from_conditions = []
        for key, value in from_properties.items():
            from_conditions.append(f"a.{key} = $from_{key}")
            
        to_conditions = []
        for key, value in to_properties.items():
            to_conditions.append(f"b.{key} = $to_{key}")
            
        from_condition_str = " AND ".join(from_conditions)
        to_condition_str = " AND ".join(to_conditions)
        
        # Create relationship
        query = f"""
        MATCH (a:{from_label}), (b:{to_label})
        WHERE {from_condition_str} AND {to_condition_str}
        CREATE (a)-[r:{relationship_type} $rel_props]->(b)
        RETURN a, r, b
        """
        
        # Prepare parameters
        parameters = {"rel_props": relationship_properties}
        for key, value in from_properties.items():
            parameters[f"from_{key}"] = value
        for key, value in to_properties.items():
            parameters[f"to_{key}"] = value
            
        result = await self.run_query_single(query, parameters, database)
        return result if result else None
    
    async def get_relationships(
        self,
        from_label: Optional[str] = None,
        from_properties: Optional[Dict[str, Any]] = None,
        to_label: Optional[str] = None,
        to_properties: Optional[Dict[str, Any]] = None,
        relationship_type: Optional[str] = None,
        relationship_properties: Optional[Dict[str, Any]] = None,
        direction: str = "OUTGOING",
        database: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get relationships between nodes.
        
        Args:
            from_label: Source node label
            from_properties: Source node properties to match
            to_label: Target node label
            to_properties: Target node properties to match
            relationship_type: Type of relationship
            relationship_properties: Properties for the relationship
            direction: Relationship direction ("OUTGOING", "INCOMING", or "BOTH")
            database: Database name
            limit: Maximum number of results to return
            
        Returns:
            List[Dict[str, Any]]: List of relationships with their connected nodes
        """
        if from_properties is None:
            from_properties = {}
        if to_properties is None:
            to_properties = {}
        if relationship_properties is None:
            relationship_properties = {}
            
        # Build match parts
        from_part = f":{from_label}" if from_label else ""
        to_part = f":{to_label}" if to_label else ""
        rel_part = f":{relationship_type}" if relationship_type else ""
        
        # Build relationship direction
        if direction == "OUTGOING":
            rel_dir = "-[r{rel_part}]->"
        elif direction == "INCOMING":
            rel_dir = "<-[r{rel_part}]-"
        else:  # BOTH
            rel_dir = "-[r{rel_part}]-"
            
        rel_dir = rel_dir.format(rel_part=rel_part)
        
        # Build match conditions
        conditions = []
        parameters = {}
        
        # Source node conditions
        for key, value in from_properties.items():
            conditions.append(f"a.{key} = $from_{key}")
            parameters[f"from_{key}"] = value
            
        # Target node conditions
        for key, value in to_properties.items():
            conditions.append(f"b.{key} = $to_{key}")
            parameters[f"to_{key}"] = value
            
        # Relationship conditions
        for key, value in relationship_properties.items():
            conditions.append(f"r.{key} = $rel_{key}")
            parameters[f"rel_{key}"] = value
            
        # Build query
        query = f"""
        MATCH (a{from_part}){rel_dir}(b{to_part})
        """
        
        if conditions:
            query += "WHERE " + " AND ".join(conditions)
            
        query += """
        RETURN a, r, b
        """
        
        if limit is not None:
            query += f"LIMIT {limit}"
            
        return await self.run_query(query, parameters, database)
    
    async def delete_relationship(
        self,
        from_label: Optional[str] = None,
        from_properties: Optional[Dict[str, Any]] = None,
        to_label: Optional[str] = None,
        to_properties: Optional[Dict[str, Any]] = None,
        relationship_type: Optional[str] = None,
        relationship_properties: Optional[Dict[str, Any]] = None,
        database: Optional[str] = None
    ) -> int:
        """
        Delete relationships between nodes.
        
        Args:
            from_label: Source node label
            from_properties: Source node properties to match
            to_label: Target node label
            to_properties: Target node properties to match
            relationship_type: Type of relationship
            relationship_properties: Properties for the relationship
            database: Database name
            
        Returns:
            int: Number of relationships deleted
        """
        if from_properties is None:
            from_properties = {}
        if to_properties is None:
            to_properties = {}
        if relationship_properties is None:
            relationship_properties = {}
            
        # Build match parts
        from_part = f":{from_label}" if from_label else ""
        to_part = f":{to_label}" if to_label else ""
        rel_part = f":{relationship_type}" if relationship_type else ""
        
        # Build match conditions
        conditions = []
        parameters = {}
        
        # Source node conditions
        for key, value in from_properties.items():
            conditions.append(f"a.{key} = $from_{key}")
            parameters[f"from_{key}"] = value
            
        # Target node conditions
        for key, value in to_properties.items():
            conditions.append(f"b.{key} = $to_{key}")
            parameters[f"to_{key}"] = value
            
        # Relationship conditions
        for key, value in relationship_properties.items():
            conditions.append(f"r.{key} = $rel_{key}")
            parameters[f"rel_{key}"] = value
            
        # Build query
        query = f"""
        MATCH (a{from_part})-[r{rel_part}]->(b{to_part})
        """
        
        if conditions:
            query += "WHERE " + " AND ".join(conditions)
            
        query += """
        DELETE r
        RETURN count(r) AS deleted
        """
        
        result = await self.run_query_single(query, parameters, database)
        return result.get('deleted', 0) if result else 0
    
    # Path and Traversal Operations
    
    async def find_paths(
        self,
        from_label: str,
        from_properties: Dict[str, Any],
        to_label: str,
        to_properties: Dict[str, Any],
        relationship_types: Optional[List[str]] = None,
        max_depth: int = 4,
        database: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find paths between two nodes.
        
        Args:
            from_label: Source node label
            from_properties: Source node properties to match
            to_label: Target node label
            to_properties: Target node properties to match
            relationship_types: List of relationship types to traverse
            max_depth: Maximum path depth
            database: Database name
            limit: Maximum number of paths to return
            
        Returns:
            List[Dict[str, Any]]: List of paths
        """
        # Build match conditions for source and target nodes
        from_conditions = []
        for key, value in from_properties.items():
            from_conditions.append(f"start.{key} = $from_{key}")
            
        to_conditions = []
        for key, value in to_properties.items():
            to_conditions.append(f"end.{key} = $to_{key}")
            
        from_condition_str = " AND ".join(from_conditions)
        to_condition_str = " AND ".join(to_conditions)
        
        # Build relationship types for path
        rel_type_str = ""
        if relationship_types:
            rel_type_str = ":" + "|:".join(relationship_types)
            
        # Build query
        query = f"""
        MATCH (start:{from_label}), (end:{to_label})
        WHERE {from_condition_str} AND {to_condition_str}
        MATCH path = shortestPath((start)-[{rel_type_str}*1..{max_depth}]->(end))
        RETURN path
        LIMIT {limit}
        """
        
        # Prepare parameters
        parameters = {}
        for key, value in from_properties.items():
            parameters[f"from_{key}"] = value
        for key, value in to_properties.items():
            parameters[f"to_{key}"] = value
            
        return await self.run_query(query, parameters, database)
    
    async def create_index(
        self,
        label: str,
        properties: List[str],
        index_name: Optional[str] = None,
        database: Optional[str] = None
    ) -> bool:
        """
        Create an index on a node label and properties.
        
        Args:
            label: Node label
            properties: List of properties to index
            index_name: Name for the index
            database: Database name
            
        Returns:
            bool: True if index was created successfully
        """
        if not index_name:
            index_name = f"idx_{label}_{'_'.join(properties)}"
            
        if len(properties) == 1:
            # Single-property index
            query = f"""
            CREATE INDEX {index_name} FOR (n:{label})
            ON (n.{properties[0]})
            """
        else:
            # Composite index
            property_list = ", ".join([f"n.{prop}" for prop in properties])
            query = f"""
            CREATE INDEX {index_name} FOR (n:{label})
            ON ({property_list})
            """
            
        try:
            await self.run_query(query, {}, database)
            return True
        except Exception as e:
            logger.error(f"Failed to create index: {str(e)}")
            return False
    
    async def create_constraint(
        self,
        label: str,
        property_name: str,
        constraint_name: Optional[str] = None,
        constraint_type: str = "UNIQUE",
        database: Optional[str] = None
    ) -> bool:
        """
        Create a constraint on a node label and property.
        
        Args:
            label: Node label
            property_name: Property for the constraint
            constraint_name: Name for the constraint
            constraint_type: Type of constraint ("UNIQUE", "EXISTS", etc.)
            database: Database name
            
        Returns:
            bool: True if constraint was created successfully
        """
        if not constraint_name:
            constraint_name = f"constraint_{label}_{property_name}_{constraint_type.lower()}"
            
        if constraint_type == "UNIQUE":
            query = f"""
            CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
            FOR (n:{label})
            REQUIRE n.{property_name} IS UNIQUE
            """
        elif constraint_type == "EXISTS":
            query = f"""
            CREATE CONSTRAINT {constraint_name} IF NOT EXISTS
            FOR (n:{label})
            REQUIRE n.{property_name} IS NOT NULL
            """
        else:
            raise ValueError(f"Unsupported constraint type: {constraint_type}")
            
        try:
            await self.run_query(query, {}, database)
            return True
        except Exception as e:
            logger.error(f"Failed to create constraint: {str(e)}")
            return False


class Neo4jTransaction:
    """
    Context manager for Neo4j transactions.
    """
    
    def __init__(
        self,
        driver: AsyncDriver,
        database: str,
        max_retry_attempts: int,
        retry_delay: float
    ):
        self._driver = driver
        self._database = database
        self._max_retry_attempts = max_retry_attempts
        self._retry_delay = retry_delay
        self._session: Optional[AsyncSession] = None
        self._tx = None
        self._tx_id = str(uuid.uuid4())
        
    async def __aenter__(self) -> 'Neo4jTransaction':
        """
        Enter the transaction context.
        """
        self._session = await self._driver.session(database=self._database).__aenter__()
        self._tx = await self._session.begin_transaction().__aenter__()
        logger.debug(f"Started Neo4j transaction {self._tx_id}")
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the transaction context.
        """
        if exc_type is None:
            # No exception, commit the transaction
            try:
                await self._tx.__aexit__(None, None, None)
                logger.debug(f"Committed Neo4j transaction {self._tx_id}")
            except Exception as e:
                logger.error(f"Error committing transaction {self._tx_id}: {str(e)}")
                raise
        else:
            # Exception occurred, rollback
            try:
                await self._tx.__aexit__(exc_type, exc_val, exc_tb)
                logger.debug(f"Rolled back Neo4j transaction {self._tx_id}")
            except Exception as e:
                logger.error(f"Error rolling back transaction {self._tx_id}: {str(e)}")
                
        # Always close the session
        if self._session:
            await self._session.__aexit__(exc_type, exc_val, exc_tb)
            self._session = None
    
    async def run(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Run a query within the transaction.
        
        Args:
            query: Cypher query
            parameters: Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        if not parameters:
            parameters = {}
            
        result = await self._tx.run(query, parameters)
        return [record.data() for record in await result.fetch_all()]
    
    async def run_single(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Run a query and return a single record.
        
        Args:
            query: Cypher query
            parameters: Query parameters
            
        Returns:
            Optional[Dict[str, Any]]: Single record or None
        """
        result = await self.run(query, parameters)
        return result[0] if result else None


# Singleton instance of the Neo4j client
neo4j_client: Optional[Neo4jClient] = None

async def init_neo4j(
    uri: str,
    username: str,
    password: str,
    database: str = "neo4j",
    max_retry_attempts: int = 3,
    retry_delay: float = 0.5,
    connection_timeout: int = 30,
    max_connection_lifetime: int = 3600,
    max_connection_pool_size: int = 50
) -> Neo4jClient:
    """
    Initialize the Neo4j client singleton.
    
    Args:
        uri: Neo4j server URI
        username: Neo4j username
        password: Neo4j password
        database: Default database name
        max_retry_attempts: Maximum number of retry attempts on failed operations
        retry_delay: Delay between retry attempts in seconds
        connection_timeout: Connection timeout in seconds
        max_connection_lifetime: Maximum lifetime of a connection in seconds
        max_connection_pool_size: Maximum size of the connection pool
        
    Returns:
        Neo4jClient: The initialized Neo4j client instance
    """
    global neo4j_client
    
    if neo4j_client is None:
        neo4j_client = Neo4jClient(
            uri=uri,
            username=username,
            password=password,
            database=database,
            max_retry_attempts=max_retry_attempts,
            retry_delay=retry_delay,
            connection_timeout=connection_timeout,
            max_connection_lifetime=max_connection_lifetime,
            max_connection_pool_size=max_connection_pool_size
        )
        await neo4j_client.connect()
    
    return neo4j_client

async def close_neo4j() -> None:
    """
    Close the Neo4j client connection.
    """
    global neo4j_client
    
    if neo4j_client:
        await neo4j_client.close()
        neo4j_client = None

async def get_neo4j() -> Neo4jClient:
    """
    Get the Neo4j client instance.
    
    Returns:
        Neo4jClient: The Neo4j client instance
    
    Raises:
        ConnectionError: If the Neo4j client has not been initialized
    """
    if neo4j_client is None:
        raise ConnectionError("Neo4j client has not been initialized. Call init_neo4j first.")
    
    return neo4j_client
