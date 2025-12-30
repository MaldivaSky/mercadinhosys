export interface Product {
    id: string;
    name: string;
    description?: string;
    barcode?: string;
    price: number;
    cost?: number;
    stock: number;
    minStock?: number;
    maxStock?: number;
    category?: string;
    brand?: string;
    isBulk?: boolean;
    unit?: string;
    createdAt: Date;
    updatedAt: Date;
}

export interface CartItem {
    id: string;
    productId: string;
    name: string;
    quantity: number;
    price: number;
    total: number;
    isBulk?: boolean;
    unit?: string;
    weight?: number;
}