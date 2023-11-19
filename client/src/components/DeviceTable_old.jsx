import {useReactTable,getCoreRowModel, flexRender, getPaginationRowModel, getSortedRowModel} from '@tanstack/react-table'

export default function DeviceTable({data}) {
    //const data = useMemo(() => MediaMetadata, [])
    
    const columns = [
        {
            header: 'Entity_ID',
            accessorKey: 'entity_id'
        },
        {
            header: 'Name',
            accessorKey: 'name'
        },
        {
            header: 'Trained',
            accessorKey: 'trained'
        },
        {
            header: 'Accuracy',
            accessorKey: 'accuracy'
        }, // Add a column with a elipsis button to show more options
        {
            header: 'Options',
            accessor: 'options'
        }
        /*{
            header: 'Options',
            id: 'options_button',
            //render: ({ row }) => (<button onClick={(e) => console.log(e, row)}>Click Me</button>)
            //render: ({ row }) => (<button onClick={(e) => this.handleButtonClick(e, row)}>Click Me</button>)
            accessor: 'id',
            Cell: ({value}) => (<button onClick={() => {console.log(value)}}>Options</button>)
        }*/

        
        
    ]

    const sub_columns = columns.slice(0)
    sub_columns.push({
        id: 'button',
        accessor: 'options',
        Cell: ({value}) => (<a onClick={() => {console.log('clicked_value', value)}}>Options</a>)
    })

    console.log('sub_columns', sub_columns, columns)


    const table = useReactTable({
        data, 
        columns, 
        getCoreRowModel:getCoreRowModel(), 
        getPaginationRowModel:getPaginationRowModel(),
        getSortedRowModel:getSortedRowModel(),
    })

    return <div>
        <table class="w3-table-all w3-hoverable">
            <thead>
                {table.getHeaderGroups().map(headerGroup => (
                    <tr key = {headerGroup.id}>
                        {headerGroup.headers.map(header => (<th key = {header.id}>
                            {flexRender(header.column.columnDef.header, header.getContext())}
                        </th>
                        ))}
                    </tr>
                ))}
            </thead>
            <tbody>
                {table.getRowModel().rows.map(row => (
                    <tr key = {row.id}>
                        {row.getVisibleCells().map(cell => (
                            <td key = {cell.id}>
                                {flexRender(cell.column.columnDef.cell, cell.getContext())}
                            </td>
                        ))}
                    </tr>
                ))}
            </tbody>
        </table>
        <div>
            <button onClick={() => table.setPageIndex(0)}>First Page</button>
            <button disabled={!table.getCanPreviousPage()} onClick={() => table.previousPage()}>Previous Page</button>
            <button disabled={!table.getCanNextPage()} onClick={() => table.nextPage()}>Next Page</button>
            <button onClick={() => table.setPageIndex(table.getPageCount() - 1)}>Last Page</button>

        </div>
    </div>
}