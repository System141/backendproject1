export interface User {
  id: string;
  name: string;
  email: string;
  phone?: string;
  role: "buyer" | "seller" | "corporate_seller" | "admin";
  status: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  user: User;
}

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

export interface Bid {
  id: string;
  auction_id: string;
  user_id: string;
  amount: number;
  created_at: string;
  user_name?: string;
  auction_title?: string;
}

export interface Payment {
  id: string;
  auction_id: string;
  buyer_id: string;
  amount: number;
  status: string;
  stripe_session_id?: string;
  created_at: string;
}

export interface SupportTicket {
  id: string;
  user_id: string;
  subject: string;
  message: string;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  created_at: string;
}