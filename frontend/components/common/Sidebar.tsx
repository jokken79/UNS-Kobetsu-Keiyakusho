'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

const navigation = [
  {
    name: 'ダッシュボード',
    href: '/',
    icon: '📊',
  },
  {
    name: '個別契約書',
    href: '/kobetsu',
    icon: '📝',
  },
  {
    name: '従業員配属',
    href: '/assign',
    icon: '👤',
  },
  {
    name: '新規契約作成',
    href: '/kobetsu/create',
    icon: '➕',
  },
  {
    name: 'データインポート',
    href: '/import',
    icon: '📥',
  },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-gray-700">
        <Link href="/" className="flex items-center gap-2">
          <span className="text-2xl">📋</span>
          <div>
            <h1 className="text-lg font-bold text-white">UNS Kobetsu</h1>
            <p className="text-xs text-gray-400">個別契約書管理</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        <ul className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href ||
              (item.href !== '/' && pathname.startsWith(item.href))

            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={`sidebar-link ${isActive ? 'active' : ''}`}
                >
                  <span className="mr-3 text-lg">{item.icon}</span>
                  <span>{item.name}</span>
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-gray-700">
        <div className="text-xs text-gray-400">
          <p>株式会社UNS企画</p>
          <p className="mt-1">許可番号: 派13-123456</p>
        </div>
      </div>
    </aside>
  )
}
