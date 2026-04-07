import {
  type ColumnDef,
  type ColumnFiltersState,
  type SortingState,
  type VisibilityState,
  flexRender,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table'
import type { Player } from '../generated/player'
import { useMemo, useState } from 'react'

interface PlayersTableProps {
  players: Player[]
  isLoading?: boolean
  error: Error | null
}

export const PlayersTable = ({ players, isLoading, error }: PlayersTableProps) => {
  const [sorting, setSorting] = useState<SortingState>([])
  const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([])
  const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({})

  const columns = useMemo<ColumnDef<Player>[]>(
    () => [
      {
        accessorKey: 'playerName',
        header: 'Name',
        cell: (info) => {
          const name = info.getValue() as string
          const row = info.row.original
          if (row.profileUrl) {
            return (
              <a
                href={row.profileUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:underline"
              >
                {name || '—'}
              </a>
            )
          }
          return name || '—'
        },
      },
      { accessorKey: 'position', header: 'Position' },
      { accessorKey: 'rating', header: 'Rating' },
      { accessorKey: 'status', header: 'Status' },
      { accessorKey: 'height', header: 'Height' },
      { accessorKey: 'weight', header: 'Weight' },
      { accessorKey: 'oldSchool', header: 'Old School' },
      { accessorKey: 'newSchool', header: 'New School' },
      { accessorKey: 'highschool', header: 'High School' },
    ],
    [],
  )

  const table = useReactTable({
    data: players,
    columns,
    state: {
      sorting,
      columnFilters,
      columnVisibility,
    },
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onColumnVisibilityChange: setColumnVisibility,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  })

  if (error) {
    return (
      <div className="rounded border border-red-200 bg-red-50 p-4 text-red-800">
        {error.message}
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="py-8 text-center text-gray-500">Loading players…</div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Column filters */}
      <div className="flex flex-wrap gap-3">
        <input
          placeholder="Filter by name…"
          value={(table.getColumn('playerName')?.getFilterValue() as string) ?? ''}
          onChange={(e) =>
            table.getColumn('playerName')?.setFilterValue(e.target.value)
          }
          className="rounded border border-gray-300 px-3 py-1.5 text-sm"
        />
        <input
          placeholder="Filter by position…"
          value={(table.getColumn('position')?.getFilterValue() as string) ?? ''}
          onChange={(e) =>
            table.getColumn('position')?.setFilterValue(e.target.value)
          }
          className="rounded border border-gray-300 px-3 py-1.5 text-sm"
        />
        <input
          placeholder="Filter by rating…"
          value={(table.getColumn('rating')?.getFilterValue() as string) ?? ''}
          onChange={(e) =>
            table.getColumn('rating')?.setFilterValue(e.target.value)
          }
          className="rounded border border-gray-300 px-3 py-1.5 text-sm"
        />
        <input
          placeholder="Filter by school…"
          value={(table.getColumn('newSchool')?.getFilterValue() as string) ?? ''}
          onChange={(e) =>
            table.getColumn('newSchool')?.setFilterValue(e.target.value)
          }
          className="rounded border border-gray-300 px-3 py-1.5 text-sm"
        />
      </div>

      <div className="overflow-x-auto rounded border border-gray-200">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-2 text-left text-xs font-medium uppercase tracking-wider text-gray-600"
                  >
                    <div
                      className={
                        header.column.getCanSort()
                          ? 'cursor-pointer select-none hover:text-gray-900'
                          : ''
                      }
                      onClick={header.column.getToggleSortingHandler()}
                    >
                      {flexRender(
                        header.column.columnDef.header,
                        header.getContext(),
                      )}
                      {{
                        asc: ' ↑',
                        desc: ' ↓',
                      }[header.column.getIsSorted() as string] ?? null}
                    </div>
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-gray-200 bg-white">
            {table.getRowModel().rows.map((row) => (
              <tr key={row.id} className="hover:bg-gray-50">
                {row.getVisibleCells().map((cell) => (
                  <td
                    key={cell.id}
                    className="whitespace-nowrap px-4 py-2 text-sm text-gray-700"
                  >
                    {flexRender(
                      cell.column.columnDef.cell,
                      cell.getContext(),
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="text-sm text-gray-500">
        Showing {table.getRowModel().rows.length} of {players.length} players
      </p>
    </div>
  )
}
