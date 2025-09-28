import React from 'react'
import Link from 'next/link'

const Navbar = () => {
  return (
    <nav className='w-full border-b-white border-b-1'>
      <div className='flex justify-between items-center py-8 text-white px-16'>
        <h1 className='font-mono font-bold text-3xl'>oParley</h1>
        <div className="flex gap-30 font-mono text-lg">
            <Link href='/'>Home</Link>
            <Link href='/'>About</Link>
            <Link href='/'>Pricing</Link>
        </div>
        <Link className='font-mono bg-primary p-2 px-9 text-black rounded-3xl' href='/login'>Login</Link>
      </div>
    </nav>
  )
}

export default Navbar
