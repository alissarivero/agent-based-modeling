export type AgentType = "searcher" | "maximizer" | "random";
export type LandscapeClass = "smooth" | "rough" | "random";
export type SocialCondition =
  | "solo"
  | "same_attract"
  | "diff_attract"
  | "same_avoid"
  | "diff_avoid";
export type SchedulerKind = "repeat_five" | "each_grid";

export interface MissionSpec {
  landscape_class: LandscapeClass;
  triplet_id: number;
  condition: SocialCondition;
  agent_a: AgentType;
  agent_b?: AgentType | null;
  scheduler: SchedulerKind;
  seed: number;
}

export interface LandscapeItem {
  triplet_id: number;
  landscape_class: LandscapeClass;
  density_mean: number;
  actual_mean: number;
  total_reward: number;
  preview: number[][];
}

export interface AgentMetrics {
  agent_id: number;
  agent_type: AgentType;
  role: string;
  reward: number;
  cells_visited: number;
  high_value_cleared: number;
  high_value_fraction: number;
  cells_seen: number;
  path: [number, number][];
}

export interface EpisodeResult {
  episode: number;
  triplet_id: number;
  landscape_class: LandscapeClass;
  steps: number;
  total_reward_available: number;
  remaining_reward: number;
  high_value_total: number;
  high_value_cleared: number;
  mean_pairwise_distance: number | null;
  constraint_violations: number;
  agents: AgentMetrics[];
  original: number[][] | null;
}

export interface SessionDebrief {
  run_id: string;
  seed: number;
  condition: SocialCondition;
  scheduler: SchedulerKind;
  landscape_class: LandscapeClass;
  triplet_id: number;
  agent_a: AgentType;
  agent_b: AgentType | null;
  n_episodes: number;
  learning_gain: number | null;
  episodes: EpisodeResult[];
}

export interface FrameAgent {
  id: number;
  type: AgentType;
  x: number;
  y: number;
  score: number;
  seen: number;
  visited: number;
}

export interface Frame {
  t: number;
  episode: number;
  triplet_id: number;
  landscape_class: LandscapeClass;
  residual: number[][] | null;
  dirty: { x: number; y: number; v: number }[];
  agents: FrameAgent[];
  constraint_ok: boolean;
  episode_done: boolean;
  session_done: boolean;
}

export interface SimConfig {
  grid: number;
  steps: number;
  vision: number;
  tau: number;
  attract_r: number;
  avoid_r: number;
}

export interface BatchSummaryRow {
  agent_type: string;
  landscape_class: string;
  condition: string;
  scheduler: string;
  reward: number;
}
