import { Link } from "react-router-dom";

export default function Navigation() {
  return (
    <nav className="fixed top-0 w-full h-16 sm:h-20 bg-setorin-green shadow-lg rounded-b-[10px] z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-12 h-full flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center">
          <img
            src="https://cdn.builder.io/api/v1/image/assets%2F29c2c2ab56d6428d903113809507fd83%2F1faf3b881558476b87c866a86a5bbd21?format=webp&width=800"
            alt="Setorin Logo"
            className="h-8 sm:h-10 w-auto"
          />
        </Link>

        {/* Navigation Links */}
        <div className="hidden md:flex items-center gap-4 lg:gap-8">
          <Link
            to="/"
            className="text-white text-base lg:text-lg font-medium hover:text-setorin-yellow transition-colors"
          >
            Home
          </Link>
          <Link
            to="/features"
            className="text-white text-base lg:text-lg font-medium hover:text-setorin-yellow transition-colors"
          >
            Features
          </Link>
          <Link
            to="/about"
            className="text-white text-base lg:text-lg font-medium hover:text-setorin-yellow transition-colors"
          >
            About Us
          </Link>
          <Link
            to="/login"
            className="text-white text-base lg:text-lg font-semibold border-2 border-white rounded-[10px] px-4 lg:px-8 py-2 lg:py-3 hover:bg-white hover:text-setorin-green transition-colors"
          >
            Login
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <button className="md:hidden text-white">
          <svg
            className="w-6 h-6"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 6h16M4 12h16M4 18h16"
            />
          </svg>
        </button>
      </div>
    </nav>
  );
}
