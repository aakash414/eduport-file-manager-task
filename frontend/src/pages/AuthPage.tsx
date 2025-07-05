import React, { useState } from 'react';
import Login from '../components/Login';
import Register from '../components/Register';

const AuthPage: React.FC = () => {
    const [isLogin, setIsLogin] = useState(true);

    const toggleForm = () => {
        setIsLogin(!isLogin);
    };

    return (
        <div className='flex flex-col gap-4 w-full p-4 justify-center items-center h-screen'>
            <div className='flex flex-col gap-4 max-w-3xl p-4'>
                <div className='flex flex-col gap-4'>{isLogin ? <Login /> : <Register />}</div>
                <button onClick={toggleForm} className='bg-blue-500 text-white p-2 rounded-md'>
                    {isLogin ? 'Need to register?' : 'Already have an account?'}
                </button>
            </div>
        </div>
    );
};

export default AuthPage;
