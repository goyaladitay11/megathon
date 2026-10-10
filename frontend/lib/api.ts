const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';

export type Health = { status: string; service: string };
export async function getHealth(): Promise<Health> {
  const response = await fetch(`${apiUrl}/health`, { cache: 'no-store' });
  if (!response.ok) throw new Error(`Backend returned ${response.status}`);
  return response.json() as Promise<Health>;
}
