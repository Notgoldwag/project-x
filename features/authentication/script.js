// Authentication Feature - Handles auth checks and user session management
(function () {
  'use strict';

  // Initialize Supabase
  const { createClient } = supabase;
  const supabaseUrl = 'https://qnbvnczctgbclolvkjcb.supabase.co';
  const supabaseKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFuYnZuY3pjdGdiY2xvbHZramNiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjI1NTg3NDIsImV4cCI6MjA3ODEzNDc0Mn0.v5t8eMJjpPtdIn6oKXshjuIH0shlztIp9fWBrRjnrGg';
  const supabaseClient = createClient(supabaseUrl, supabaseKey);

  // Make supabase client available globally to avoid multiple instances
  window.supabaseClient = supabaseClient;

  // DOM elements
  const authLoading = document.getElementById('auth-loading');
  const mainContent = document.getElementById('main-content');
  const profileInitials = document.getElementById('profile-initials');
  const profileEmail = document.getElementById('profile-email');
  const signOutBtn = document.getElementById('sign-out-btn');

  // Auth guard - check session on page load
  async function checkAuth() {
    try {
      const { data: { session }, error } = await supabaseClient.auth.getSession();

      if (error) {
        console.error('Auth error:', error);
        redirectToLogin();
        return;
      }

      if (!session) {
        redirectToLogin();
        return;
      }

      // User is authenticated
      showMainContent(session.user);
    } catch (error) {
      console.error('Auth check failed:', error);
      redirectToLogin();
    }
  }

  // Redirect to login page
  function redirectToLogin() {
    window.location.href = '/login_signup';
  }

  // Show main content and set up profile
  function showMainContent(user) {
    // Hide loading overlay
    authLoading.classList.add('hidden');

    // Show main content
    mainContent.classList.remove('hidden');

    // Set up profile icon
    setupProfile(user);
  }

  // Set up profile information
  function setupProfile(user) {
    // Set initials
    const email = user.email;
    const fullName = user.user_metadata?.full_name || email;

    let initials = '';
    if (fullName && fullName !== email) {
      // Extract initials from full name
      const nameParts = fullName.split(' ');
      initials = nameParts.map(part => part.charAt(0).toUpperCase()).join('');
      if (initials.length > 2) initials = initials.substring(0, 2);
    } else {
      // Use first character of email
      initials = email.charAt(0).toUpperCase();
    }

    profileInitials.textContent = initials;
    profileEmail.textContent = email;
    profileEmail.title = email; // Full email on hover
  }

  // Sign out handler
  async function handleSignOut() {
    try {
      const { error } = await supabaseClient.auth.signOut();

      if (error) {
        console.error('Sign out error:', error);
      }

      // Redirect to index page
      window.location.href = '/';
    } catch (error) {
      console.error('Sign out failed:', error);
      // Force redirect even if sign out fails
      window.location.href = '/';
    }
  }

  // Listen for auth state changes
  supabaseClient.auth.onAuthStateChange((event, session) => {
    if (event === 'SIGNED_OUT' || !session) {
      window.location.href = '/';
    }
  });

  // Event listeners
  if (signOutBtn) {
    signOutBtn.addEventListener('click', handleSignOut);
  }

  // Initialize auth check
  checkAuth();
})();
