import type React from "react";
import { useAuth } from "../contexts/AuthContext";
import { Navigate } from "react-router-dom";

const Redirect: React.FC = () => {
    const user = useAuth();
    if (user) {
        return <Navigate to="/dashboard" replace />
    } else {
        return <Navigate to="/login" replace />
    }
}

export default Redirect