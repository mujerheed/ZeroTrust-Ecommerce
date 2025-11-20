import Link from "next/link"import Image from "next/image";

import { Button } from "@/components/ui/button"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"export default function Home() {

  return (

export default function Home() {    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">

  return (      <main className="flex min-h-screen w-full max-w-3xl flex-col items-center justify-between py-32 px-16 bg-white dark:bg-black sm:items-start">

    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-50">        <Image

      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">          className="dark:invert"

        <p className="fixed left-0 top-0 flex w-full justify-center border-b border-gray-300 bg-gradient-to-b from-zinc-200 pb-6 pt-8 backdrop-blur-2xl dark:border-neutral-800 dark:bg-zinc-800/30 dark:from-inherit lg:static lg:w-auto  lg:rounded-xl lg:border lg:bg-gray-200 lg:p-4 lg:dark:bg-zinc-800/30">          src="/next.svg"

          TrustGuard Zero Trust E-commerce          alt="Next.js logo"

        </p>          width={100}

      </div>          height={20}

          priority

      <div className="relative flex place-items-center before:absolute before:h-[300px] before:w-[480px] before:-translate-x-1/2 before:rounded-full before:bg-gradient-to-br before:from-transparent before:to-blue-700 before:opacity-10 before:blur-2xl before:content-[''] after:absolute after:-z-20 after:h-[180px] after:w-[240px] after:translate-x-1/3 after:bg-gradient-to-t after:from-blue-900 after:via-blue-900 after:blur-2xl after:content-[''] before:dark:bg-gradient-to-br before:dark:from-transparent before:dark:to-blue-700 before:dark:opacity-10 after:dark:from-blue-900 after:dark:via-[#0141ff] after:dark:opacity-40 before:lg:h-[360px] z-[-1]">        />

        <h1 className="text-6xl font-bold text-center mb-8 text-blue-900">TrustGuard</h1>        <div className="flex flex-col items-center gap-6 text-center sm:items-start sm:text-left">

      </div>          <h1 className="max-w-xs text-3xl font-semibold leading-10 tracking-tight text-black dark:text-zinc-50">

            To get started, edit the page.tsx file.

      <div className="mb-32 grid text-center lg:max-w-5xl lg:w-full lg:mb-0 lg:grid-cols-2 lg:text-left gap-8">          </h1>

        <Card className="hover:shadow-lg transition-shadow">          <p className="max-w-md text-lg leading-8 text-zinc-600 dark:text-zinc-400">

          <CardHeader>            Looking for a starting point or more instructions? Head over to{" "}

            <CardTitle>Vendor Portal</CardTitle>            <a

            <CardDescription>              href="https://vercel.com/templates?framework=next.js&utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"

              Manage orders, negotiate prices, and verify receipts.              className="font-medium text-zinc-950 dark:text-zinc-50"

            </CardDescription>            >

          </CardHeader>              Templates

          <CardContent>            </a>{" "}

            <Link href="/vendor/login">            or the{" "}

              <Button className="w-full">Login as Vendor</Button>            <a

            </Link>              href="https://nextjs.org/learn?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"

          </CardContent>              className="font-medium text-zinc-950 dark:text-zinc-50"

        </Card>            >

              Learning

        <Card className="hover:shadow-lg transition-shadow">            </a>{" "}

          <CardHeader>            center.

            <CardTitle>CEO Portal</CardTitle>          </p>

            <CardDescription>        </div>

              Oversee business, manage vendors, and approve high-value transactions.        <div className="flex flex-col gap-4 text-base font-medium sm:flex-row">

            </CardDescription>          <a

          </CardHeader>            className="flex h-12 w-full items-center justify-center gap-2 rounded-full bg-foreground px-5 text-background transition-colors hover:bg-[#383838] dark:hover:bg-[#ccc] md:w-[158px]"

          <CardContent>            href="https://vercel.com/new?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"

            <div className="space-y-2">            target="_blank"

              <Link href="/ceo/login">            rel="noopener noreferrer"

                <Button className="w-full" variant="default">Login as CEO</Button>          >

              </Link>            <Image

              <Link href="/ceo/signup">              className="dark:invert"

                <Button className="w-full" variant="outline">Sign Up as CEO</Button>              src="/vercel.svg"

              </Link>              alt="Vercel logomark"

            </div>              width={16}

          </CardContent>              height={16}

        </Card>            />

      </div>            Deploy Now

    </main>          </a>

  )          <a

}            className="flex h-12 w-full items-center justify-center rounded-full border border-solid border-black/[.08] px-5 transition-colors hover:border-transparent hover:bg-black/[.04] dark:border-white/[.145] dark:hover:bg-[#1a1a1a] md:w-[158px]"

            href="https://nextjs.org/docs?utm_source=create-next-app&utm_medium=appdir-template-tw&utm_campaign=create-next-app"
            target="_blank"
            rel="noopener noreferrer"
          >
            Documentation
          </a>
        </div>
      </main>
    </div>
  );
}
