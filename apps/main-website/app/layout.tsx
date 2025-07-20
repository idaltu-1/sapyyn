import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ThemeProvider } from '@mui/material/styles'
import CssBaseline from '@mui/material/CssBaseline'
import { ToastContainer } from 'react-toastify'
import 'react-toastify/dist/ReactToastify.css'
import theme from '../lib/theme'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Sapyyn - Patient Referral System',
  description: 'Bridging the Gap Between Providers and Patients Nationwide',
  keywords: 'dental referral, patient referral, healthcare, dentist, specialist',
  authors: [{ name: 'Sapyyn Team' }],
  openGraph: {
    title: 'Sapyyn - Patient Referral System',
    description: 'Bridging the Gap Between Providers and Patients Nationwide',
    url: 'https://sapyyn.com',
    siteName: 'Sapyyn',
    images: [
      {
        url: '/images/og-image.jpg',
        width: 1200,
        height: 630,
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Sapyyn - Patient Referral System',
    description: 'Bridging the Gap Between Providers and Patients Nationwide',
    images: ['/images/twitter-image.jpg'],
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <ThemeProvider theme={theme}>
          <CssBaseline />
          {children}
          <ToastContainer
            position="top-right"
            autoClose={5000}
            hideProgressBar={false}
            newestOnTop={false}
            closeOnClick
            rtl={false}
            pauseOnFocusLoss
            draggable
            pauseOnHover
          />
        </ThemeProvider>
      </body>
    </html>
  )
}