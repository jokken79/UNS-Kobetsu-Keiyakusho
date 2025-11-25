import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '@/styles/globals.css'
import { Providers } from './providers'
import { Sidebar } from '@/components/common/Sidebar'
import { Header } from '@/components/common/Header'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'UNS Kobetsu Keiyakusho | 個別契約書管理システム',
  description: '労働者派遣法第26条に準拠した個別契約書管理システム',
  keywords: ['派遣契約', '個別契約書', '労働者派遣法', 'UNS企画'],
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ja">
      <body className={`${inter.className} antialiased`}>
        <Providers>
          <div className="min-h-screen bg-gray-50">
            {/* Sidebar */}
            <Sidebar />

            {/* Main Content */}
            <div className="lg:ml-72 min-h-screen flex flex-col">
              {/* Header */}
              <Header />

              {/* Page Content */}
              <main className="flex-1 p-4 lg:p-6 pt-20 lg:pt-6">
                <div className="animate-fade-in">
                  {children}
                </div>
              </main>

              {/* Footer */}
              <footer className="py-4 px-6 text-center text-sm text-gray-500 border-t border-gray-200 bg-white">
                <p>&copy; {new Date().getFullYear()} 株式会社UNS企画. All rights reserved.</p>
              </footer>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  )
}
