import { createTamagui, createTokens } from 'tamagui'
import { bodyFont, headingFont } from './fonts'
import { animations } from './animations'
import { themes } from './themes'
import { tokens as defaultTokens } from '@tamagui/themes'

const tokens = createTokens({
  ...defaultTokens,
})

export const config = createTamagui({
  animations,
  fonts: {
    body: bodyFont,
    heading: headingFont,
  },
  themes,
  tokens,
})
