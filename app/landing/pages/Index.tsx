import Navigation from "@/components/Navigation";
import { Link } from "react-router-dom";

// SVG Icons for features
const DuitinIcon = () => (
  <svg
    width="177"
    height="177"
    viewBox="0 0 197 197"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="drop-shadow-lg"
  >
    <g filter="url(#filter0_d_162_751)">
      <circle cx="98.5" cy="96.5" r="88.5" fill="#016F2F" />
    </g>
    <ellipse cx="99.1938" cy="97.1813" rx="26.2096" ry="26.2096" fill="#FFE200" />
    <path
      d="M136.53 122.948C142.555 114.226 145.329 103.667 144.368 93.1101C143.407 82.5533 138.773 72.6683 131.273 65.1774C123.772 57.6866 113.881 53.0648 103.323 52.1176C92.7652 51.1704 82.2095 53.9577 73.4955 59.9939M136.53 122.948L131.362 110.041M136.53 122.948L150.894 117.191M61.8987 71.6448C55.9048 80.3756 53.161 90.9314 54.1447 101.476C55.1283 112.02 59.7771 121.887 67.2824 129.358C74.7878 136.83 84.6747 141.434 95.2236 142.37C105.772 143.306 116.316 140.515 125.019 134.482M61.8987 71.6448L67.0401 84.4742M61.8987 71.6448L47.6447 77.3571"
      stroke="#67DF99"
      strokeWidth="10"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <defs>
      <filter id="filter0_d_162_751" x="0" y="0" width="197" height="197" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
        <feFlood floodOpacity="0" result="BackgroundImageFix" />
        <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha" />
        <feOffset dy="2" />
        <feGaussianBlur stdDeviation="5" />
        <feComposite in2="hardAlpha" operator="out" />
        <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0" />
        <feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow_162_751" />
        <feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow_162_751" result="shape" />
      </filter>
    </defs>
  </svg>
);

const TemuinIcon = () => (
  <svg
    width="177"
    height="177"
    viewBox="0 0 197 197"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="drop-shadow-lg"
  >
    <g filter="url(#filter0_d_162_752)">
      <circle cx="98.5" cy="96.5" r="88.5" fill="#016F2F" />
    </g>
    <path
      d="M98.7475 139.808C89.4088 139.785 80.3744 136.486 73.2185 130.486C66.0626 124.485 61.2388 116.164 59.5878 106.973C59.0856 99.7387 59.8633 85.2705 66.9917 85.2705"
      stroke="#67DF99"
      strokeWidth="10"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M100.781 139.808C110.12 139.785 119.154 136.486 126.31 130.486C133.466 124.485 138.29 116.164 139.941 106.973C140.443 99.7387 139.665 85.2705 132.537 85.2705"
      stroke="#67DF99"
      strokeWidth="10"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <path
      d="M99.7642 82.4812C97.7425 82.4812 95.8036 81.678 94.374 80.2485C92.9445 78.8189 92.1413 76.88 92.1413 74.8583C92.1413 72.8365 92.9445 70.8976 94.374 69.4681C95.8036 68.0385 97.7425 67.2354 99.7642 67.2354C101.786 67.2354 103.725 68.0385 105.154 69.4681C106.584 70.8976 107.387 72.8365 107.387 74.8583C107.387 75.8593 107.19 76.8506 106.807 77.7754C106.424 78.7003 105.862 79.5406 105.154 80.2485C104.447 80.9563 103.606 81.5178 102.681 81.9009C101.757 82.284 100.765 82.4812 99.7642 82.4812ZM99.7642 53.5142C94.1034 53.5142 88.6745 55.7629 84.6717 59.7657C80.6689 63.7685 78.4201 69.1975 78.4201 74.8583C78.4201 90.8663 99.7642 114.497 99.7642 114.497C99.7642 114.497 121.108 90.8663 121.108 74.8583C121.108 69.1975 118.86 63.7685 114.857 59.7657C110.854 55.7629 105.425 53.5142 99.7642 53.5142Z"
      fill="#FFE200"
    />
    <defs>
      <filter id="filter0_d_162_752" x="0" y="0" width="197" height="197" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
        <feFlood floodOpacity="0" result="BackgroundImageFix" />
        <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha" />
        <feOffset dy="2" />
        <feGaussianBlur stdDeviation="5" />
        <feComposite in2="hardAlpha" operator="out" />
        <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0" />
        <feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow_162_752" />
        <feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow_162_752" result="shape" />
      </filter>
    </defs>
  </svg>
);

const RobinIcon = () => (
  <svg
    width="177"
    height="177"
    viewBox="0 0 197 197"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    className="drop-shadow-lg"
  >
    <g filter="url(#filter0_d_162_770)">
      <circle cx="98.5" cy="96.5" r="88.5" fill="#016F2F" />
    </g>
    <path
      d="M98.494 53C89.0188 53 79.5436 53.2525 70.7001 53.8838C65.0873 54.2482 59.7923 56.616 55.7804 60.5556C51.7685 64.4953 49.3068 69.7444 48.8441 75.3463C47.8334 88.855 47.707 102.238 48.5914 115.746C49.0757 121.75 51.8242 127.345 56.2806 131.4C60.7371 135.455 66.5687 137.667 72.5952 137.588H85.8604V121.175H72.5952C68.6788 121.301 65.2677 118.524 64.8887 114.61C64.1307 101.985 64.257 89.36 65.1414 76.735C65.394 73.2 68.1734 70.5488 71.7108 70.2963C80.3016 69.665 89.3978 69.4125 98.494 69.4125C107.59 69.4125 116.686 69.7913 125.277 70.17C128.688 70.4225 131.594 73.0738 131.847 76.6088C132.857 89.2337 132.857 101.859 132.099 114.484C131.594 118.397 128.309 121.301 124.393 121.175H111.128L85.8604 137.588V154L111.128 137.588H124.393C136.9 137.714 147.386 128.119 148.397 115.746C149.281 102.364 149.155 88.855 148.27 75.4725C147.807 69.8707 145.346 64.6215 141.334 60.6819C137.322 56.7422 132.027 54.3744 126.414 54.01C117.444 53.2525 107.969 53 98.494 53Z"
      fill="#67DF99"
    />
    <path
      d="M89.1973 108.531C89.1973 107.961 89.6869 107.487 90.2745 107.487C90.4104 107.492 90.5438 107.524 90.6662 107.582C93.1142 108.626 95.7581 109.243 98.451 109.29C101.144 109.243 103.788 108.673 106.236 107.629C106.367 107.573 106.509 107.543 106.653 107.541C106.796 107.539 106.939 107.566 107.072 107.619C107.204 107.672 107.325 107.751 107.425 107.851C107.525 107.950 107.604 108.069 107.656 108.199C107.754 108.294 107.803 108.389 107.803 108.531V112.233C107.803 112.755 107.509 113.23 107.019 113.467C104.375 114.701 101.438 115.366 98.5 115.461C95.5623 115.366 92.6246 114.701 89.9807 113.467C89.4911 113.23 89.1973 112.755 89.1973 112.233V108.531Z"
      fill="#FFE200"
    />
    <circle cx="84.5346" cy="89.5307" r="6.20939" fill="#FFE200" />
    <path
      d="M93.3801 95.6355C94.8075 93.5692 95.4647 91.0676 95.2371 88.5666C95.0095 86.0655 93.9116 83.7236 92.1346 81.9489C90.3577 80.1742 88.0144 79.0793 85.513 78.8549C83.0117 78.6305 80.5109 79.2908 78.4465 80.7209M93.3801 95.6355L92.1559 92.5778M93.3801 95.6355L96.7833 94.2717M75.699 83.4811C74.279 85.5496 73.629 88.0504 73.862 90.5485C74.095 93.0467 75.1964 95.3841 76.9745 97.1542C78.7526 98.9243 81.095 100.015 83.5941 100.237C86.0933 100.459 88.5911 99.7974 90.6532 98.3681M75.699 83.4811L76.9171 86.5206M75.699 83.4811L72.3221 84.8345"
      stroke="#67DF99"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <circle cx="115.776" cy="90.2105" r="11.9605" fill="#FFE200" />
    <path
      d="M120.673 93.557C121.479 92.39 121.851 90.9771 121.722 89.5645C121.593 88.1519 120.973 86.8292 119.97 85.8269C118.966 84.8246 117.643 84.2062 116.23 84.0794C114.817 83.9527 113.405 84.3256 112.239 85.1333M120.673 93.557L119.982 91.83M120.673 93.557L122.595 92.7867M110.687 86.6923C109.885 87.8605 109.518 89.273 109.649 90.6839C109.781 92.0948 110.403 93.415 111.407 94.4148C112.412 95.4145 113.735 96.0306 115.146 96.1559C116.558 96.2811 117.968 95.9076 119.133 95.1003M110.687 86.6923L111.375 88.409M110.687 86.6923L108.78 87.4566"
      stroke="#67DF99"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
    <defs>
      <filter id="filter0_d_162_770" x="0" y="0" width="197" height="197" filterUnits="userSpaceOnUse" colorInterpolationFilters="sRGB">
        <feFlood floodOpacity="0" result="BackgroundImageFix" />
        <feColorMatrix in="SourceAlpha" type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 127 0" result="hardAlpha" />
        <feOffset dy="2" />
        <feGaussianBlur stdDeviation="5" />
        <feComposite in2="hardAlpha" operator="out" />
        <feColorMatrix type="matrix" values="0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0.25 0" />
        <feBlend mode="normal" in2="BackgroundImageFix" result="effect1_dropShadow_162_770" />
        <feBlend mode="normal" in="SourceGraphic" in2="effect1_dropShadow_162_770" result="shape" />
      </filter>
    </defs>
  </svg>
);

export default function Index() {
  return (
    <div className="min-h-screen relative bg-white pt-16 sm:pt-20">
      {/* Navigation */}
      <Navigation />

      {/* Hero Section */}
      <section className="relative h-[600px] md:h-[700px] lg:h-[800px] overflow-hidden">
        <img
          src="https://api.builder.io/api/v1/image/assets/TEMP/a0222ff573a2698875da586f0871ca65fa0bf241?width=2560"
          alt="Background"
          className="w-full h-full object-cover"
        />
        
        {/* Hero Content */}
        <div className="absolute inset-0 flex items-center bg-black/20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
            <div className="max-w-3xl">
              
    
              
              {/* Main Headline */}
              <div className="space-y-3 mb-6">
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white font-inter leading-tight">
                  setorin sampah,
                </h1>
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-setorin-yellow font-inter leading-tight">
                  dapatin rupiah!
                </h1>
              </div>

              {/* Subtitle */}
              <p className="text-white text-lg sm:text-xl lg:text-2xl font-medium mb-8 leading-relaxed max-w-2xl">
                Platform digital yang mengubah sampah terpilah Anda menjadi saldo nyata. Mudah, cepat, dan menguntungkan.
              </p>

              {/* Call to Action Buttons */}
              <div className="flex flex-col sm:flex-row gap-4">
                <Link
                  to="/login"
                  className="bg-setorin-yellow hover:bg-yellow-400 text-setorin-green font-bold py-4 px-8 rounded-lg text-lg transition-colors duration-200 text-center"
                >
                  Mulai Sekarang
                </Link>
                <Link
                  to="/features"
                  className="bg-transparent border-2 border-white text-white hover:bg-white hover:text-setorin-green font-bold py-4 px-8 rounded-lg text-lg transition-colors duration-200 text-center"
                >
                  Pelajari Lebih Lanjut
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 text-center">
            <div className="space-y-2">
              <div className="text-4xl lg:text-5xl font-bold text-setorin-green">10K+</div>
              <div className="text-lg text-gray-600">Pengguna Aktif</div>
            </div>
            <div className="space-y-2">
              <div className="text-4xl lg:text-5xl font-bold text-setorin-green">50K+</div>
              <div className="text-lg text-gray-600">Botol Plastik Terkumpul</div>
            </div>
            <div className="space-y-2">
              <div className="text-4xl lg:text-5xl font-bold text-setorin-green">10 Juta Kg</div>
              <div className="text-lg text-gray-600">CO2 Dihindari</div>
            </div>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-20 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-setorin-green mb-4">
              Cara Kerja Setorin
            </h2>
            <p className="text-xl text-gray-600 max-w-3xl mx-auto">
              Tiga langkah sederhana untuk mengubah sampah Anda menjadi rupiah
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            {/* Step 1 */}
            <div className="text-center space-y-6">
              <div className="w-20 h-20 bg-setorin-green rounded-full flex items-center justify-center mx-auto">
                <span className="text-3xl font-bold text-white">1</span>
              </div>
              <h3 className="text-2xl font-bold text-setorin-green">Kumpulkan Sampah</h3>
              <p className="text-gray-600 leading-relaxed">
                Pilah dan kumpulkan botol plastik atau sampah daur ulang lainnya di rumah Anda.
              </p>
            </div>

            {/* Step 2 */}
            <div className="text-center space-y-6">
              <div className="w-20 h-20 bg-setorin-green rounded-full flex items-center justify-center mx-auto">
                <span className="text-3xl font-bold text-white">2</span>
              </div>
              <h3 className="text-2xl font-bold text-setorin-green">Temukan SmartBin</h3>
              <p className="text-gray-600 leading-relaxed">
                Gunakan fitur Temuin untuk menemukan lokasi SmartBin terdekat dari Anda.
              </p>
            </div>

            {/* Step 3 */}
            <div className="text-center space-y-6">
              <div className="w-20 h-20 bg-setorin-green rounded-full flex items-center justify-center mx-auto">
                <span className="text-3xl font-bold text-white">3</span>
              </div>
              <h3 className="text-2xl font-bold text-setorin-green">Dapatkan Rupiah</h3>
              <p className="text-gray-600 leading-relaxed">
                Masukkan sampah ke SmartBin dan dapatkan saldo rupiah langsung ke akun Anda.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-setorin-green py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section Title */}
          <h2 className="text-white text-3xl sm:text-4xl lg:text-5xl font-bold text-center mb-16 font-inter">
            Fitur Utama
          </h2>

          {/* Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 lg:gap-16">
            {/* Duitin Feature */}
            <div className="text-center space-y-6">
              <div className="flex justify-center">
                <DuitinIcon />
              </div>
              <h3 className="text-white text-2xl lg:text-3xl font-bold font-inter">
                Duitin
              </h3>
              <p className="text-white text-lg lg:text-xl font-medium leading-relaxed max-w-sm mx-auto">
                Ubah setiap botol plastik rupiah sungguhan di Duitin ke akun Anda setelah setiap setoran
              </p>
            </div>

            {/* Temuin Feature */}
            <div className="text-center space-y-6">
              <div className="flex justify-center">
                <TemuinIcon />
              </div>
              <h3 className="text-white text-2xl lg:text-3xl font-bold font-inter">
                Temuin
              </h3>
              <p className="text-white text-lg lg:text-xl font-medium leading-relaxed max-w-sm mx-auto">
                Peta interaktif yang akan memandumu ke lokasi SmartBin terdekat secara real-time
              </p>
            </div>

            {/* Robin Feature */}
            <div className="text-center space-y-6">
              <div className="flex justify-center">
                <RobinIcon />
              </div>
              <h3 className="text-white text-2xl lg:text-3xl font-bold font-inter">
                Robin
              </h3>
              <p className="text-white text-lg lg:text-xl font-medium leading-relaxed max-w-sm mx-auto">
                Asisten AI personal Anda yang ramah dan selalu siap 24/7 untuk menjawab semua tentang Setorin
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section className="py-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-setorin-green mb-4">
              Apa Kata Pengguna
            </h2>
            <p className="text-xl text-gray-600">
              Ribuan pengguna telah merasakan manfaat Setorin
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Testimonial 1 */}
            <div className="bg-gray-50 p-8 rounded-lg">
              <div className="text-setorin-yellow text-2xl mb-4">★★★★★</div>
              <p className="text-gray-600 mb-6 italic">
                "Setorin benar-benar mengubah cara pandang saya terhadap sampah. Sekarang sampah rumah tangga bisa jadi penghasilan tambahan!"
              </p>
              <div className="font-bold text-setorin-green">Sarah, Jakarta</div>
            </div>

            {/* Testimonial 2 */}
            <div className="bg-gray-50 p-8 rounded-lg">
              <div className="text-setorin-yellow text-2xl mb-4">★★★★★</div>
              <p className="text-gray-600 mb-6 italic">
                "Aplikasinya mudah digunakan dan SmartBin-nya tersebar di mana-mana. Sudah dapat Rp 200,000 dalam sebulan!"
              </p>
              <div className="font-bold text-setorin-green">Ahmad, Bandung</div>
            </div>

            {/* Testimonial 3 */}
            <div className="bg-gray-50 p-8 rounded-lg">
              <div className="text-setorin-yellow text-2xl mb-4">★★★★★</div>
              <p className="text-gray-600 mb-6 italic">
                "Konsep yang brilliant! Lingkungan jadi bersih dan kita dapat keuntungan. Robin juga sangat membantu!"
              </p>
              <div className="font-bold text-setorin-green">Siti, Surabaya</div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-gradient-to-r from-setorin-green to-green-600">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
            Siap Mulai Mengubah Sampah Jadi Rupiah?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Bergabunglah dengan ribuan pengguna lainnya dan rasakan manfaatnya hari ini!
          </p>
          <Link
            to="/login"
            className="bg-setorin-yellow hover:bg-yellow-400 text-setorin-green font-bold py-4 px-10 rounded-lg text-xl transition-colors duration-200 inline-block"
          >
            Daftar Sekarang Gratis
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {/* Logo and Description */}
            <div className="md:col-span-2">
              <img 
                src="https://cdn.builder.io/api/v1/image/assets%2F29c2c2ab56d6428d903113809507fd83%2F4cd41da3e2cf4583a502c506744da796?format=webp&width=800" 
                alt="Setorin Logo" 
                className="h-8 w-auto mb-4 brightness-0 invert"
              />
              <p className="text-gray-400 max-w-md">
                Platform digital yang mengubah sampah terpilah Anda menjadi saldo nyata. 
                Mudah, cepat, dan menguntungkan untuk semua.
              </p>
            </div>

            {/* Quick Links */}
            <div>
              <h3 className="text-lg font-bold mb-4">Quick Links</h3>
              <ul className="space-y-2">
                <li><Link to="/" className="text-gray-400 hover:text-white transition-colors">Home</Link></li>
                <li><Link to="/features" className="text-gray-400 hover:text-white transition-colors">Features</Link></li>
                <li><Link to="/about" className="text-gray-400 hover:text-white transition-colors">About Us</Link></li>
                <li><Link to="/login" className="text-gray-400 hover:text-white transition-colors">Login</Link></li>
              </ul>
            </div>

            {/* Contact */}
            <div>
              <h3 className="text-lg font-bold mb-4">Contact</h3>
              <ul className="space-y-2 text-gray-400">
                <li>Email: info@setorin.com</li>
                <li>Phone: +62 21 1234 5678</li>
                <li>Jakarta, Indonesia</li>
              </ul>
            </div>
          </div>

          <div className="border-t border-gray-800 mt-12 pt-8 text-center text-gray-400">
            <p>&copy; 2024 Setorin. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
