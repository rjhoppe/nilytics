import { type Player, Player as PlayerCodec } from '../generated/player'

const API_BASE = '/api'

export async function fetchPlayers(): Promise<Player[]> {
  const res = await fetch(`${API_BASE}/players`)
  if (!res.ok) {
    throw new Error(`Failed to fetch players: ${res.status} ${res.statusText}`)
  }
  const json = await res.json() as unknown[]
  return json.map((item) => PlayerCodec.fromJSON(item))
}
