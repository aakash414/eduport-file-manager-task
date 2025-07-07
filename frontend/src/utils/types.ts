// src/utils/types.ts

export interface ProgressEvent {
    loaded: number;
    total: number;
}

export interface User {
    id: number;
    username: string;
    email: string;
}

export interface FileUpload {
    id: number;
    original_filename: string;
    description?: string;
    file_type: string;
    file_size: number;
    file_size_display: string;
    upload_date: string;
    last_accessed: string | null;
    file_url: string;
    content_preview_url?: string;
    uploaded_by: string;
}



export interface SearchParams {
    [key: string]: any;
    search?: string;
    file_types?: string[];
    start_date?: string;
    end_date?: string;
    min_size?: number;
    max_size?: number;
    page?: number;
    page_size?: number;
    cursor?: string;
    detailed?: boolean;
    preview?: boolean;
    include?: string[];
}

export interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}
