import '@tamagui/core/reset.css'
import '@tamagui/font-inter/css/400.css'
import '@tamagui/font-inter/css/700.css'
import 'raf/polyfill'

import type React from 'react'
import Head from 'next/head'
import type { SolitoAppProps } from 'solito'
import { NextTamaguiProvider } from 'app/provider/NextTamaguiProvider'
import { config } from '@my/ui'

if (process.env.NODE_ENV === 'production') {
  require('../public/tamagui.css')
}

import { ApiProvider } from 'app/provider/api'

import { AuthGuard } from 'app/provider/AuthGuard'

import { useAuthStore } from 'app/store/auth'
import { ToastProvider, ToastViewport } from '@my/ui'

function MyApp({ Component, pageProps }: SolitoAppProps) {
  const { theme } = useAuthStore()

  return (
    <>
      <Head>
        <title>Tamagui • Pages Router</title>
        <meta
          name="description"
          content="Tamagui, Solito, Expo & Next.js"
        />
        <link
          rel="icon"
          href="/favicon.ico"
        />
        <style
          dangerouslySetInnerHTML={{
            // the first time this runs you'll get the full CSS including all themes
            // after that, it will only return CSS generated since the last call
            __html: config.getNewCSS(),
          }}
        />

        <style
          dangerouslySetInnerHTML={{
            __html: config.getCSS({
              // if you are using "outputCSS" option, you should use this "exclude"
              // if not, then you can leave the option out
              exclude: process.env.NODE_ENV === 'production' ? 'design-system' : null,
            }),
          }}
        />

        <script
          dangerouslySetInnerHTML={{
            // avoid flash of animated things on enter:
            __html: `document.documentElement.classList.add('t_unmounted')`,
          }}
        />
      </Head>
      <NextTamaguiProvider defaultTheme={theme}>
        <ToastProvider>
          <ApiProvider>
            <AuthGuard>
              <Component {...pageProps} />
            </AuthGuard>
          </ApiProvider>
          <ToastViewport />
        </ToastProvider>
      </NextTamaguiProvider>
    </>
  )
}

export default MyApp
