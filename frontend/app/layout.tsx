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
      <body className={inter.className}>
        <Providers>
          <div className="flex h-screen bg-gray-100">
            {/* Sidebar */}
            <Sidebar />

            {/* Main Content */}
            <div className="flex-1 flex flex-col ml-64">
              {/* Header */}
              <Header />

              {/* Page Content */}
              <main className="flex-1 overflow-auto p-6">
                {children}
              </main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  )
}
