import { Outlet } from 'react-router-dom'
import Navigation from './Navigation'

const Layout = () => {
  return (
    <div className="min-h-screen bg-background">
      <Navigation />
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-6 max-w-6xl">
        <div className="text-center">
          <Outlet />
        </div>
      </main>
    </div>
  )
}

export default Layout