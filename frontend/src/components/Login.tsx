import React, { useState } from 'react';
import axios, { AxiosError } from 'axios';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        try {
            await axios.post('http://localhost:8000/api/users/login/', {
                username,
                password,
            }, {
                withCredentials: true
            });
            navigate('/home');
        } catch (err) {
            const error = err as AxiosError<{ error: string }>;
            if (error.response && error.response.data) {
                setError(error.response.data.error);
            } else {
                setError('Login failed. Please try again.');
            }
            console.error('Login failed', error);
        }
    };

    return (
        <form onSubmit={handleSubmit} className='flex flex-col gap-4'>
            <h2>Login</h2>
            {error && <p className="text-red-500">{error}</p>}
            <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Username"
                required
                className='border border-gray-300 rounded-md p-2 bg-gray-950'
            />
            <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
                required
                className='border border-gray-300 rounded-md p-2 bg-gray-950'
            />
            <button type="submit">Login</button>
        </form>
    );
};

export default Login;
