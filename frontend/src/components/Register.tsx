import React, { useState } from 'react';
import axios, { AxiosError } from 'axios';
import { useNavigate } from 'react-router-dom';

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
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErrors({});
        try {
            await axios.post('http://localhost:8000/api/users/register/', {
                username,
                email,
                password,
            }, {
                withCredentials: true
            });
            navigate('/login');
        } catch (err) {
            const error = err as AxiosError<RegisterError>;
            if (error.response && error.response.data) {
                setErrors(error.response.data);
            } else {
                setErrors({ non_field_errors: ['Registration failed. Please try again.'] });
            }
            console.error('Registration failed', error);
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
            <button type="submit">Register</button>
        </form>
    );
};

export default Register;
