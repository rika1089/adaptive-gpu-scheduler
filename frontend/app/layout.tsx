import './globals.css'
import { Sidebar } from '@/components/layout/Sidebar'
import { Topbar } from '@/components/layout/Topbar'

export const metadata = { title: 'GPU Scheduler Dashboard' }

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        <div className="app-layout">
          <Sidebar />
          <div className="main-wrap">
            <Topbar />
            <main className="page-content">
              {children}
            </main>
          </div>
        </div>
      </body>
    </html>
  )
}
