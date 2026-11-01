export default function ProtectedRoute({ isAuthenticated, fallback, children }) {
  return isAuthenticated ? children : fallback
}
