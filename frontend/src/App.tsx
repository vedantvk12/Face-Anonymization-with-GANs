import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import Navbar from './components/Navbar';
import Workspace from './pages/Workspace';
import EvaluationPage from './pages/EvaluationPage';
import About from './pages/About';
import { useEffect, useState } from 'react';
import { DEFAULT_HEALTH_STATUS, getHealth } from './services/api';
import type { HealthStatus } from './services/api';

const Layout = () => {
  const [health, setHealth] = useState<HealthStatus>(DEFAULT_HEALTH_STATUS);

  useEffect(() => {
    let active = true;

    const refreshHealth = async () => {
      try {
        const result = await getHealth();
        if (active) setHealth(result);
      } catch (error) {
        console.error('Health check failed:', error);
        if (active) {
          setHealth({ ...DEFAULT_HEALTH_STATUS, status: 'offline', message: 'Backend unavailable' });
        }
      }
    };

    refreshHealth();
    const interval = window.setInterval(refreshHealth, 5000);

    return () => {
      active = false;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <div className="min-h-screen flex flex-col relative z-0">
      <Navbar health={health} />
      <main className="flex-1 w-full max-w-[1400px] mx-auto px-6 py-8 relative z-10">
        <Outlet />
      </main>
    </div>
  );
};

const router = createBrowserRouter([
  {
    path: '/',
    element: <Layout />,
    children: [
      { path: 'workspace', element: <Workspace /> },
      { path: 'evaluation', element: <EvaluationPage /> },
      { path: 'about', element: <About /> },
      { path: '/', element: <Navigate to="/workspace" replace /> },
    ],
  },
]);

function App() {
  return <RouterProvider router={router} />;
}

export default App;
