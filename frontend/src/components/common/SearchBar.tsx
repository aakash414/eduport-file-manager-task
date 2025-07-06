// src/components/common/SearchBar.tsx
import React, { useState } from 'react';

interface SearchBarProps {
    onSearch: (query: string) => void;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch }) => {
    const [query, setQuery] = useState('');

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        onSearch(query);
    };

    return (
        <form onSubmit={handleSearch} className="flex mb-4">
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search files..."
                className="border border-gray-300 rounded-l-md p-2 flex-grow bg-gray-150"
            />
            <button type="submit" className="bg-blue-500 text-white rounded-r-md px-4">
                Search
            </button>
        </form>
    );
};

export default SearchBar;
