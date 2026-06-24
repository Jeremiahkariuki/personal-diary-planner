# 🔐 Social Authentication Setup Guide

This guide provides professional, step-by-step instructions to configure **Google** and **Facebook** social login for the Jdiary Planner.

---

## 🚀 1. Google OAuth Configuration

1.  **Google Cloud Console:** Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2.  **New Project:** Create a new project named `Jdiary Planner`.
3.  **OAuth Consent Screen:**
    *   Set User Type to **External**.
    *   Provide App name, support email, and developer contact info.
    *   Add the `.../auth/userinfo.email` and `.../auth/userinfo.profile` scopes.
4.  **Credentials:**
    *   Create **OAuth 2.0 Client ID**.
    *   Application type: **Web application**.
    *   **Authorized JavaScript origins:** `http://127.0.0.1:8000` (and your production domain).
    *   **Authorized redirect URIs:** `http://127.0.0.1:8000/accounts/google/login/callback/`.
5.  **Save Credentials:** Copy the **Client ID** and **Client Secret**.

---

## 🚀 2. Facebook OAuth Configuration

1.  **Meta for Developers:** Go to [Meta for Developers](https://developers.facebook.com/).
2.  **Create App:** Select **Allow people to log in with their Facebook account**.
3.  **App Setup:**
    *   Go to **Settings > Basic**.
    *   Add **App Domains**: `127.0.0.1`.
    *   Add **Privacy Policy URL** (can use a placeholder like `http://127.0.0.1:8000/privacy` for dev).
4.  **Facebook Login:**
    *   Add the **Facebook Login** product.
    *   Go to **Settings > Client OAuth Settings**.
    *   **Valid OAuth Redirect URIs:** `http://127.0.0.1:8000/accounts/facebook/login/callback/`.
5.  **Save Credentials:** Copy the **App ID** and **App Secret**.

---

## 🛠️ 3. Integrating with Jdiary

Once you have the credentials, you can add them to the application using one of the following methods:

### Method A: Environment Variables (Recommended)
Add the following to your `.env` file:
```env
GOOGLE_CLIENT_ID=your_id_here
GOOGLE_CLIENT_SECRET=your_secret_here
FACEBOOK_APP_ID=your_id_here
FACEBOOK_APP_SECRET=your_secret_here
```

### Method B: Django Admin Panel
1.  Navigate to `http://127.0.0.1:8000/admin/`.
2.  Go to **Social Accounts > Social Applications**.
3.  Add a new Social Application:
    *   **Provider:** Google (or Facebook).
    *   **Name:** Jdiary Google Login.
    *   **Client id:** Your ID.
    *   **Secret key:** Your Secret.
    *   **Sites:** Select `example.com` (SITE_ID 1) and move it to the right box.

---

## ✅ Verification
1.  Navigate to the Login or Register page.
2.  Click the **Google** or **Facebook** button.
3.  You should be redirected to the provider's login screen.
4.  Upon successful login, you will be redirected back to the Jdiary Dashboard.
