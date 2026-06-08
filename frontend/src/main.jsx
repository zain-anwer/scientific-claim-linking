import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.jsx";

// Render the main App component inside the root element of the HTML
createRoot(document.getElementById("root")).render(
  <StrictMode><App /></StrictMode>
);