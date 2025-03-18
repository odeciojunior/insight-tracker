import 'package:firebase_auth/firebase_auth.dart';
import 'package:get/get.dart';
import '../../core/config/routes.dart';

class AuthController extends GetxController {
  final FirebaseAuth _auth = FirebaseAuth.instance;
  final Rx<User?> user = Rx<User?>(null);
  
  @override
  void onInit() {
    super.onInit();
    user.bindStream(_auth.authStateChanges());
    ever(user, _initialScreen);
  }
  
  void _initialScreen(User? user) {
    if (user == null) {
      Get.offAllNamed(AppRoutes.LOGIN);
    } else {
      Get.offAllNamed(AppRoutes.HOME);
    }
  }
  
  Future<void> register(String email, String password) async {
    try {
      await _auth.createUserWithEmailAndPassword(
        email: email.trim(),
        password: password.trim(),
      );
    } catch (e) {
      Get.snackbar(
        'Registration Error',
        e.toString(),
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }
  
  Future<void> login(String email, String password) async {
    try {
      await _auth.signInWithEmailAndPassword(
        email: email.trim(),
        password: password.trim(),
      );
    } catch (e) {
      Get.snackbar(
        'Login Error',
        e.toString(),
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }
  
  Future<void> logout() async {
    try {
      await _auth.signOut();
    } catch (e) {
      Get.snackbar(
        'Logout Error',
        e.toString(),
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }
  
  Future<void> resetPassword(String email) async {
    try {
      await _auth.sendPasswordResetEmail(email: email.trim());
      Get.snackbar(
        'Password Reset',
        'Password reset link sent to your email',
        snackPosition: SnackPosition.BOTTOM,
      );
    } catch (e) {
      Get.snackbar(
        'Password Reset Error',
        e.toString(),
        snackPosition: SnackPosition.BOTTOM,
      );
    }
  }
  
  bool isLoggedIn() {
    return user.value != null;
  }
}
