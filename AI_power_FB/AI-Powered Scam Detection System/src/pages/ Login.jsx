import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();
  const location = useLocation();

  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleChange = (event) => {
    const { name, value } = event.target;

    setFormData((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");

    if (!formData.email.trim() || !formData.password) {
      setError("Email and password are required.");
      return;
    }

    try {
      setLoading(true);

      const response = await fetch(
        "http://127.0.0.1:8000/auth/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: formData.email.trim(),
            password: formData.password,
          }),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Invalid email or password."
        );
      }

      // Store JWT
      localStorage.setItem(
        "access_token",
        data.access_token
      );

      // Return to the page the user originally requested
      const redirectPath =
        location.state?.from?.pathname || "/dashboard";

      navigate(redirectPath, {
        replace: true,
      });

    } catch (err) {
      setError(
        err.message || "Login failed. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center px-4">

      <div className="w-full max-w-md">

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-lg p-8">

          {/* Header */}
          <div className="text-center mb-8">

            <h1 className="text-3xl font-bold text-gray-900">
              Welcome Back
            </h1>

            <p className="mt-2 text-gray-600">
              Login to ScamShield AI
            </p>

          </div>

          {/* Error */}
          {error && (
            <div
              className="mb-5 p-3 rounded-lg bg-red-50
                         border border-red-200 text-red-700 text-sm"
              role="alert"
            >
              {error}
            </div>
          )}

          {/* Form */}
          <form
            onSubmit={handleSubmit}
            className="space-y-5"
          >

            {/* Email */}
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Email
              </label>

              <input
                id="email"
                name="email"
                type="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="Enter your email"
                autoComplete="email"
                disabled={loading}
                required
                className="w-full px-4 py-3 border border-gray-300
                           rounded-lg focus:outline-none
                           focus:ring-2 focus:ring-blue-500
                           focus:border-blue-500
                           disabled:bg-gray-100"
              />
            </div>

            {/* Password */}
            <div>
              <label
                htmlFor="password"
                className="block text-sm font-semibold text-gray-700 mb-2"
              >
                Password
              </label>

              <input
                id="password"
                name="password"
                type="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="Enter your password"
                autoComplete="current-password"
                disabled={loading}
                required
                className="w-full px-4 py-3 border border-gray-300
                           rounded-lg focus:outline-none
                           focus:ring-2 focus:ring-blue-500
                           focus:border-blue-500
                           disabled:bg-gray-100"
              />
            </div>

            {/* Login */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4
                         bg-blue-600 text-white
                         font-semibold rounded-lg
                         hover:bg-blue-700
                         disabled:bg-gray-400
                         disabled:cursor-not-allowed
                         transition"
            >
              {loading ? "Logging in..." : "Login"}
            </button>

          </form>

          {/* Register */}
          <div className="mt-6 text-center">

            <p className="text-sm text-gray-600">
              Don't have an account?{" "}
              <Link
                to="/register"
                className="font-semibold text-blue-600 hover:text-blue-700"
              >
                Create an account
              </Link>
            </p>

          </div>

        </div>

        {/* Security notice */}
        <p className="mt-4 text-center text-xs text-gray-500">
          Never share your password, OTP, PIN, or other
          sensitive information.
        </p>

      </div>

    </div>
  );
}

export default Login;