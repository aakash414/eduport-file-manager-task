// src/utils/types.ts

export interface User {
    id: number;
    username: string;
    email: string;
}

export interface FileUpload {
    id: number;
    original_filename: string;
    file_size: number;
    file_type: string;
    upload_date: string;
    description?: string;
    last_accessed?: string;
    uploaded_by: User;
}

export interface FileShareLink {
    id: number;
    file_upload: number;
    token: string;
    expires_at?: string;
    created_at: string;
    access_count: number;
}

export interface FileAccessLog {
    id: number;
    file_upload: number;
    user?: User;
    share_link?: number;
    timestamp: string;
    access_type: string;
    ip_address?: string;
    user_agent?: string;
}

export interface PaginatedResponse<T> {
    pagination: {
        count: number;
        current_page: number;
        total_pages: number;
        page_size: number;
        has_next: boolean;
        has_previous: boolean;
    };
    results: T[];
}
