import React, { useState, useEffect } from 'react';
import { AxiosError } from 'axios';
import apiClient from '../api/axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface RegisterError {
    username?: string[];
    email?: string[];
    password?: string[];
    non_field_errors?: string[];
}

const Register: React.FC = () => {
    const [username, setUsername] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [errors, setErrors] = useState<RegisterError>({});
    const [loading, setLoading] = useState(false);
    const navigate = useNavigate();
    const { login, isAuthenticated } = useAuth();

    useEffect(() => {
        if (isAuthenticated) {
            navigate('/dashboard');
        }
    }, [isAuthenticated, navigate]);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErrors({});
        setLoading(true);
        try {
            const response = await apiClient.post('/users/register/', {
                username,
                email,
                password,
            });
            login(response.data);
        } catch (err) {
            const error = err as AxiosError<RegisterError>;
            if (error.response && error.response.data) {
                setErrors(error.response.data);
            } else {
                setErrors({ non_field_errors: ['Registration failed. Please try again.'] });
            }
            console.error('Registration failed', error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <form onSubmit={handleSubmit} className='flex flex-col gap-4'>
            <h2>Register</h2>
            {errors.non_field_errors && <p className="text-red-500">{errors.non_field_errors.join(', ')}</p>}
            <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                required
                className='border border-gray-300 rounded-md p-2 bg-gray-150'
            />
            {errors.username && <p className="text-red-500">{errors.username.join(', ')}</p>}
            <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
                required
                className='border border-gray-300 rounded-md p-2 bg-gray-150'
            />
            {errors.email && <p className="text-red-500">{errors.email.join(', ')}</p>}
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                className='border border-gray-300 rounded-md p-2 bg-gray-150'
            />
            {errors.password && <p className="text-red-500">{errors.password.join(', ')}</p>}
            <button type="submit" disabled={loading}>
                {loading ? 'Registering...' : 'Register'}
            </button>
        </form>
    );
};

export default Register;
