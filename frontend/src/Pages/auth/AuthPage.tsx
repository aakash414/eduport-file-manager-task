import React, { useState } from 'react';
import Login from '../../components/Login';
import Register from '../../components/Register';

const AuthPage: React.FC = () => {
    const [isLogin, setIsLogin] = useState(true);

    const toggleForm = () => {
        setIsLogin(!isLogin);
    };

    return (
        <div className='flex flex-col gap-4'>
            {isLogin ? <Login /> : <Register />}
            <button onClick={toggleForm}>
                {isLogin ? 'Need to register?' : 'Already have an account?'}
            </button>
        </div>
    );
};

export default AuthPage;
