import "server-only";
import OpenAI from "openai";

export const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
export const MODEL = "gpt-4o-mini";
export const MAX_TOKENS = 800;
