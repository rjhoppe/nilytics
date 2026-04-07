import { useQuery } from '@tanstack/react-query'
import { fetchPlayers } from './api/players'
import { PlayersTable } from './components/PlayersTable'

const App = () => {
  const { data: players = [], isLoading, error } = useQuery({
    queryKey: ['players'],
    queryFn: fetchPlayers,
  })

  return (
    <div className="min-h-screen bg-gray-50 p-4 font-sans">
      <h1 className="mb-6 text-2xl font-semibold text-gray-900">Nilytics</h1>
      <PlayersTable
        players={players}
        isLoading={isLoading}
        error={error instanceof Error ? error : null}
      />
    </div>
  )
}

export default App
