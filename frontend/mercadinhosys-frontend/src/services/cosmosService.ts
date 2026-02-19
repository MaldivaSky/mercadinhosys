import { apiClient } from '../api/apiClient';

export interface CosmosProductData {
    gtin: number;
    description: string;
    brand: {
        name: string;
        picture: string;
    };
    ncm: {
        code: string;
        description: string;
        full_description: string;
    };
    gpc: {
        code: string;
        description: string;
    };
    price: string;
    avg_price: number;
    max_price: number;
    thumbnail: string;
    width: number;
    height: number;
    length: number;
    net_weight: number;
    gross_weight: number;
}

export const cosmosService = {
    async buscarPorGtin(gtin: string): Promise<CosmosProductData> {
        const response = await apiClient.get<CosmosProductData>(`/produtos/cosmos/${gtin}`);
        return response.data;
    }
};
