import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom';
import Navbar from './components/Navbar';
import Workspace from './pages/Workspace';
import EvaluationPage from './pages/EvaluationPage';
import About from './pages/About';
import { useEffect, useState } from 'react';
import { getHealth } from './services/api';
import type { HealthStatus } from './services/api';

const Layout = () => {
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch(console.error);
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
