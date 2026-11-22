import { NavLink, Outlet } from 'react-router-dom';
import { navigation } from './navigation.js';

export default function AppLayout() {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>OfflineTrace</h1>
        <p className="muted">Secure document workflow</p>
        <nav>
          {navigation.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === '/'}>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="main-content"><Outlet /></main>
    </div>
  );
}
