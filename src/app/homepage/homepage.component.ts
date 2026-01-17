import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';

type Product = {
  id: number;
  name: string;
  price: number;
  originalPrice?: number;
  rating: number;
  reviews: number;
  tag: string;
  category: string;
  description: string;
  swatches: string[];
  gradient: string;
  badge?: string;
};

type Collection = {
  id: number;
  title: string;
  description: string;
  cta: string;
  gradient: string;
};

type Testimonial = {
  id: number;
  quote: string;
  name: string;
  title: string;
};

@Component({
  selector: 'app-homepage',
  imports: [CommonModule],
  templateUrl: './homepage.component.html',
  styleUrl: './homepage.component.scss'
})
export class HomepageComponent implements OnInit {
  ngOnInit(): void {

  }
  readonly navLinks = ['New in', 'Apparel', 'Footwear', 'Accessories', 'Outlet'];
  readonly categories = ['All', 'Everyday', 'Work', 'Travel', 'Outdoor'];

  readonly products: Product[] = [
    {
      id: 1,
      name: 'Lumen Knit Sneakers',
      price: 128,
      originalPrice: 160,
      rating: 4.8,
      reviews: 312,
      tag: 'Best Seller',
      category: 'Everyday',
      description: 'Breathable knit with a cloudfoam core.',
      swatches: ['#f4b4a5', '#b7d8e3', '#233345'],
      gradient: 'linear-gradient(135deg, #f4b4a5, #f6e0d6)',
      badge: '20% off'
    },
    {
      id: 2,
      name: 'Atlas Utility Tote',
      price: 94,
      rating: 4.6,
      reviews: 188,
      tag: 'New',
      category: 'Travel',
      description: 'Water resistant canvas with modular pockets.',
      swatches: ['#22313f', '#c9b08f', '#7f5f4b'],
      gradient: 'linear-gradient(135deg, #c9b08f, #f0e1c6)'
    },
    {
      id: 3,
      name: 'Solstice Workwear Jacket',
      price: 214,
      rating: 4.9,
      reviews: 89,
      tag: 'Limited',
      category: 'Work',
      description: 'Structured silhouette with recycled insulation.',
      swatches: ['#1d1d1f', '#7d8f9b', '#d7c3a1'],
      gradient: 'linear-gradient(135deg, #1d1d1f, #5a6a72)'
    },
    {
      id: 4,
      name: 'Terra Trail Backpack',
      price: 142,
      rating: 4.7,
      reviews: 221,
      tag: 'Outdoor',
      category: 'Outdoor',
      description: 'Lightweight frame with smart hydration pocket.',
      swatches: ['#1a2a2f', '#6b8f71', '#c1b49a'],
      gradient: 'linear-gradient(135deg, #6b8f71, #d8e1cc)'
    },
    {
      id: 5,
      name: 'Aurora Lounge Set',
      price: 110,
      rating: 4.5,
      reviews: 402,
      tag: 'Cozy pick',
      category: 'Everyday',
      description: 'Soft brushed fleece made for slow days.',
      swatches: ['#c9b8c3', '#e7d2b9', '#607482'],
      gradient: 'linear-gradient(135deg, #c9b8c3, #efe4ea)'
    },
    {
      id: 6,
      name: 'Monarch Leather Slides',
      price: 98,
      rating: 4.4,
      reviews: 147,
      tag: 'Fan favorite',
      category: 'Everyday',
      description: 'Supple leather with hand-stitched detail.',
      swatches: ['#3a2a23', '#b08968', '#e9d7c3'],
      gradient: 'linear-gradient(135deg, #b08968, #f0d9c2)'
    }
  ];

  readonly collections: Collection[] = [
    {
      id: 1,
      title: 'City Layers',
      description: 'Sharpen your daily uniform with modular outerwear.',
      cta: 'Shop jackets',
      gradient: 'linear-gradient(140deg, #c4c9c9, #f1f5f4)'
    },
    {
      id: 2,
      title: 'Weekend Escape',
      description: 'Packable essentials that move from trail to town.',
      cta: 'Shop travel',
      gradient: 'linear-gradient(140deg, #c2b8a3, #f7f0e4)'
    }
  ];

  readonly perks = [
    {
      title: 'Free carbon-neutral shipping',
      detail: 'Delivered in 2 to 4 days with reusable packaging.'
    },
    {
      title: 'Buy now, pay later',
      detail: 'Split into 4 payments with zero fees.'
    },
    {
      title: 'Loyalty studio',
      detail: 'Members get early access and private drops.'
    }
  ];

  readonly testimonials: Testimonial[] = [
    {
      id: 1,
      quote:
        'The quality is unreal. Every detail feels considered, from the stitch to the packaging.',
      name: 'Amira Holt',
      title: 'Product Designer'
    },
    {
      id: 2,
      quote:
        'I packed for a two-week trip with just the capsule collection. Everything worked.',
      name: 'Liam Chen',
      title: 'Travel Writer'
    },
    {
      id: 3,
      quote: 'Finally a brand that is stylish and practical in the same breath.',
      name: 'Jordan Vale',
      title: 'Creative Lead'
    }
  ];

  isDiscounted(p: Product): boolean {
    return !!p.originalPrice && p.originalPrice > p.price;
  }
}
