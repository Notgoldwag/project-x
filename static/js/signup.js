// Import Supabase client
import { createClient } from "https://cdn.jsdelivr.net/npm/@supabase/supabase-js/+esm";

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("WealthifyRegister");

  // Supabase configuration
  const supabaseUrl = "https://qnbvnczctgbclolvkjcb.supabase.co";
  const supabaseKey = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFuYnZuY3pjdGdiY2xvbHZramNiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI1NTg3NDIsImV4cCI6MjA3ODEzNDc0Mn0.v5t8eMJjpPtdIn6oKXshjuIH0shlztIp9fWBrRjnrGg";
  const supabase = createClient(supabaseUrl, supabaseKey);

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    if (validateForm()) {
      const fullName = document.getElementById("fullName").value.trim();
      const email = document.getElementById("emailCreate").value.trim();
      const password = document.getElementById("passwordCreate").value.trim();

      try {
        // Create user in Supabase Auth
        const { data, error: signUpError } = await supabase.auth.signUp({
          email,
          password,
          options: {
            data: { full_name: fullName } // store metadata
          }
        });

        if (signUpError) throw signUpError;

        // Some setups require email confirmation, so user may be null here
        const userId = data.user?.id || data.session?.user?.id;
        if (!userId) {
          showModal(
            "Account created! Please check your email to confirm your account before logging in."
          );
          return;
        }

        // Insert into 'users' table
        const { error: dbError } = await supabase
          .from("Users")
          .insert([{ id: userId, full_name: fullName, email }]);

        if (dbError) throw dbError;

        showModal("Account Registered! Redirecting to Login...");

        setTimeout(() => {
          window.location.href = "/login_signup";
        }, 2000);
      } catch (error) {
        showModal("Error signing up: " + error.message);
        console.error(error);
      }
    }
  });

  // Validation functions
  function validateForm() {
    const fullName = document.getElementById("fullName").value.trim();
    const email = document.getElementById("emailCreate").value.trim();
    const password = document.getElementById("passwordCreate").value.trim();

    if (fullName === "") {
      showModal("Please enter your full name.");
      return false;
    }
    if (email === "" || !isValidEmail(email)) {
      showModal("Please enter a valid email address.");
      return false;
    }
    if (!isValidPassword(password)) {
      showModal(
        "Password must be at least 6 characters long, contain at least one uppercase letter, and one special character."
      );
      return false;
    }
    return true;
  }

  // Helpers
  function showModal(message) {
    document.getElementById("modalMessage").innerText = message;
    document.getElementById("customModal").style.display = "block";
    document.getElementById("modalBackdrop").style.display = "block";
  }

  function isValidEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
  }

  function isValidPassword(password) {
    return /^(?=.*[A-Z])(?=.*[!@#$%^&*(),.?":{}|<>])[A-Za-z\d!@#$%^&*(),.?":{}|<>]{6,}$/.test(
      password
    );
  }
});
