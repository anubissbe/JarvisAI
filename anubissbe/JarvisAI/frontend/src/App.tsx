# ... existing code ...

// Pages
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Settings from './pages/Settings';
import Knowledge from './pages/Knowledge';
import NotFound from './pages/NotFound';

# ... existing code ...

<Route path="/knowledge" element={
  <ProtectedRoute>
    <Knowledge />
  </ProtectedRoute>
} />

# ... existing code ...