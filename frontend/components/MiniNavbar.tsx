import React from 'react'
import Link from 'next/link'

const Navbar = () => {
  return (
    <nav className='w-'>
      <div className='flex justify-between items-center py-8 text-white px-16'>
        <Link href='/' className='font-mono font-bold text-3xl'>oParley</Link>
        <Link className='font-mono bg-primary p-2 px-9 text-black rounded-3xl' href='/login'>Login</Link>
      </div>
    </nav>
  )
}

export default Navbar
