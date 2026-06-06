import { NavLink } from 'react-router-dom';

const linkClass = ({ isActive }) =>
  `rounded-md px-3 py-2 text-sm font-semibold transition ${
    isActive ? 'bg-white/15 text-white' : 'text-blue-100 hover:bg-white/10 hover:text-white'
  }`;

export default function Navbar() {
  return (
    <header className="bg-blue-700 shadow-sm">
      <nav className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
        <NavLink to="/" className="text-lg font-bold text-white">
          AI Appointment Automation
        </NavLink>
        <div className="flex gap-2">
          <NavLink to="/" end className={linkClass}>Dashboard</NavLink>
          <NavLink to="/create" className={linkClass}>New Appointment</NavLink>
        </div>
      </nav>
    </header>
  );
}
