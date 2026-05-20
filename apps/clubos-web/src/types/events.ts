export type EventCategory =
  | "player_signing"
  | "player_departure"
  | "match_result_win"
  | "match_result_loss"
  | "trophy_win"
  | "trophy_loss"
  | "transfer_window"
  | "media_event"
  | "injury_news"
  | "commercial_event";

export type ImpactMagnitude = "high" | "medium" | "low";

export interface EventSchema {
  event_id: string;
  event_date: string;
  event_name: string;
  event_category: EventCategory;
  event_description: string;
  expected_impact: string; // Comma-separated
  affected_assets: string[];
  impact_magnitude: ImpactMagnitude;
}

export interface EventCreateSchema {
  event_date: string;
  event_name: string;
  event_category: EventCategory;
  event_description: string;
  expected_impact: string;
  impact_magnitude: ImpactMagnitude;
}

export interface EventListResponse {
  total_count: number;
  items: EventSchema[];
}
