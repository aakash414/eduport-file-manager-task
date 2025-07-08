import React, { useState, useRef, useEffect } from 'react';
import { FiLogOut } from 'react-icons/fi';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

const Header: React.FC = () => {
    const [isDropdownOpen, setDropdownOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const navigate = useNavigate();
    const { user, logout } = useAuth();
    const getInitials = (name: string) => {

        return name ? name.charAt(0).toUpperCase() : '';
    };

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setDropdownOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, [dropdownRef]);

    const handleSignOut = () => {
        logout();
        setDropdownOpen(false);
        navigate('/login');
    };

    if (!user) {
        return null;
    }
    return (
        <header className="sticky top-0 z-30 w-full px-8 py-4 bg-white/80 backdrop-blur-sm shadow-sm">
            <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                    <h1 className="text-xl font-bold text-gray-800">File Manager</h1>
                </div>

                <div className="relative">
                    <div
                        className="flex items-center space-x-3 cursor-pointer"
                        onClick={() => setDropdownOpen(!isDropdownOpen)}
                    >
                        <div className="w-10 h-10 rounded-full bg-blue-600 flex items-center justify-center">
                            <span className="text-white font-bold">{getInitials(user.username)}</span>
                        </div>

                    </div>
                    {isDropdownOpen && (
                        <div
                            ref={dropdownRef}
                            className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg z-10 border border-gray-200"
                        >
                            <div className="p-3 border-b border-gray-200">
                                <p className="font-semibold text-sm text-gray-800">{user.username}</p>
                                <p className="text-xs text-gray-500">{user.email}</p>
                            </div>
                            <div className="py-1">
                                <button
                                    onClick={handleSignOut}
                                    className="flex items-center w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                >
                                    <FiLogOut className="w-4 h-4 mr-2" />
                                    Sign Out
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
};

export default Header;