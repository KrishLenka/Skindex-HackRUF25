import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import ComponentLibrary from "./components/ComponentLibrary";
import ImageUpload from "./components/ImageUpload";
import { Activity, Upload, MessageCircle, Library } from "lucide-react";
import Home from "@/components/ui/Home";   // ← points to the file you just made


/**
 * Simple, single Header component (no breadcrumb, no search box).
 * @returns {JSX.Element} The Header component.
 */
const Header = () => (
  <header className="bg-white border-b-2 border-blue-800">
    <div className="w-full px-4">
      <div className="flex items-center justify-between py-4">
        <div className="flex items-center">
          <div className="w-12 h-12 bg-blue-800 flex items-center justify-center mr-4">
            <Activity className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-blue-800 leading-tight">DermAI</h1>
            <p className="text-sm text-gray-600 leading-tight">Your trusted AI dermatology consultant</p>
          </div>
        </div>
      </div>

      <nav className="border-t border-gray-300 py-2">
        <div className="flex space-x-8 text-sm">
          {/* Home removed - defaults to Image Analysis */}
          <Link to="/" className="text-blue-800 hover:text-blue-900 font-medium py-2">
            <Upload className="w-4 h-4 inline mr-2" /> Image Analysis
          </Link>
          <Link to="/assistant" className="text-blue-800 hover:text-blue-900 font-medium py-2">
            <MessageCircle className="w-4 h-4 inline mr-2" /> Clinical Assistant
          </Link>
        </div>
      </nav>
    </div>
  </header>
);


<Routes>
  <Route path="/" element={<Home />} />
  <Route path="/analyze" element={<ImageUpload />} />
</Routes>

/**
 * Root Application component.
 * @returns {JSX.Element} The main App component.
 */
function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<ImageUpload />} />
          {/* Clinical Assistant removed */}
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;