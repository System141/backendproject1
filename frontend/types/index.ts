export interface AuctionImage {
  id: string;
  image_url: string;
  sort_order: number;
}

export interface Auction {
  id: string;
  title: string;
  current_price: number;
  end_time: string;
  status: string;
  start_price: number;
  category_id: number;
  brand?: string;
  model?: string;
  year?: number;
  mileage?: number;
  fuel_type?: string;
  transmission?: string;
  damage_status?: string;
  equipment_brand?: string;
  serial_number?: string;
  condition?: string;
  location?: string;
  images?: AuctionImage[];
}