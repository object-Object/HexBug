export interface ActivityHexPattern extends APIHexPattern {
  lookup: boolean;
}

export interface ActivityHexPatternResponse extends APIHexPattern {
  name: string | null;
}

export interface APIHexPattern {
  direction:
    | "NORTH_EAST"
    | "EAST"
    | "SOUTH_EAST"
    | "SOUTH_WEST"
    | "WEST"
    | "NORTH_WEST";
  signature: string;
}

export async function postActivityPatterns({
  patterns,
  api_token,
}: {
  patterns: ActivityHexPattern[];
  api_token: string;
}): Promise<ActivityHexPatternResponse[]> {
  const response = await fetch("/api/activity/patterns", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${api_token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(patterns),
  });
  return (await response.json()) as ActivityHexPatternResponse[];
}
