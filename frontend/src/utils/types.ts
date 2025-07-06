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
    file: string;
    original_filename: string;
    description: string;
    file_type: string;
    file_size: number;
    upload_date: string;
    last_accessed: string;
    view_count: number;
    is_duplicate: boolean;
    permissions?: {
        can_download: boolean;

        can_delete: boolean;
    };
    uploaded_by: User;
}



export interface SearchParams {
    [key: string]: any;
    query?: string;
    file_type?: string[];
    start_date?: string;
    end_date?: string;
    size_min?: number;
    size_max?: number;
    page?: number;
    page_size?: number;
}

export interface PaginatedResponse<T> {
    count: number;
    next: string | null;
    previous: string | null;
    results: T[];
}
