//General requirements and/or suggestions for Noesis plugins:
//
// -Use 1-byte struct alignment for all shared structures. (plugin MSVC project file defaults everything to 1-byte-aligned)
// -Always clean up after yourself. Your plugin stays in memory the entire time Noesis is loaded, so you don't want to crap up the process heaps.
// -Try to use reliable type-checking, to ensure your plugin doesn't conflict with other file types and create false-positive situations.
// -Really try not to write crash-prone logic in your data check function! This could lead to Noesis crashing from trivial things like the user browsing files.
// -When using the rpg begin/end interface, always make your Vertex call last, as it's the function which triggers a push of the vertex with its current attributes.
// -!!!! Check the web site and documentation for updated suggestions/info! !!!!

//This plugin was written entirely with a shitty hex viewer and specs from The Doom Wiki - http://doom.wikia.com/wiki/

//Excuse the mess. I spent a day stubbing this out a year or two ago, then spent a day finishing it up this weekend. Changes
//in my various styles and conventions are at war with each other. Creating convex polygons from subsectors also turned out
//to not be quite as straightforward as I'd hoped, so that's all rather hacked to shit at the moment. Also, I haven't been
//bothered to make a proper 2D vector class and functions so there's some horrible C-ness there with more code duplication
//than one might enjoy.

#include "stdafx.h"
#include "doomwad.h"

const char *g_pPluginName = "doom_wad_maps";
const char *g_pPluginDesc = "Doom map/wad handler, by Dick.";

int g_fmtHandle = -1;
wadOpts_t *g_opts = NULL;

//novel super-hacky idea. most partition lines overlap linedefs that are still in the map, and the real
//problem with precision loss is in the directional component. if we can match a node's partition line
//to a linedef, we can use the verts to calculate a new high-precision direction.
#define RECOVER_NODE_PARTITION_PRECISION 2

static inline void convenient_set_color(noeRAPI_t *rapi, float r, float g, float b)
{
	float clr[4] = {r, g, b, 1.0f};
	rapi->rpgVertColor4f(clr);
}

static inline void debug_render_line(noeRAPI_t *rapi, float *v1, float *v2, float z = 0.0f, float lineWidth = 8.0f, float gradHax = 0.0f)
{
	RichVec3 pos1(v1[0], v1[1], z);
	RichVec3 pos2(v2[0], v2[1], z);
	RichVec3 dir = (pos2-pos1);
	dir.Normalize();
	//RichVec3 sideDir = dir.Cross(RichVec3(0.0f, 0.0f, 1.0f));
	RichVec3 sideDir(dir[1], -dir[0], 0.0f);

	rapi->rpgBegin(RPGEO_QUAD_ABC_ACD);
	if (gradHax != 0.0f)
	{
		convenient_set_color(rapi, 1.0f, 0.0f, gradHax);
		rapi->rpgVertex3f((pos1+sideDir*lineWidth).v);
		convenient_set_color(rapi, 1.0f, 1.0f, gradHax);
		rapi->rpgVertex3f((pos2+sideDir*lineWidth).v);
		rapi->rpgVertex3f((pos2-sideDir*lineWidth).v);
		convenient_set_color(rapi, 1.0f, 0.0f, gradHax);
		rapi->rpgVertex3f((pos1-sideDir*lineWidth).v);
	}
	else
	{
		rapi->rpgVertex3f((pos1+sideDir*lineWidth).v);
		rapi->rpgVertex3f((pos2+sideDir*lineWidth).v);
		rapi->rpgVertex3f((pos2-sideDir*lineWidth).v);
		rapi->rpgVertex3f((pos1-sideDir*lineWidth).v);
	}
	rapi->rpgEnd();
}

static inline void debug_render_line(noeRAPI_t *rapi, short *v1, short *v2, float z = 0.0f, float lineWidth = 8.0f, float gradHax = 0.0f)
{
	float fv1[2] = { float(v1[0]), float(v1[1]) };
	float fv2[2] = { float(v2[0]), float(v2[1]) };
	debug_render_line(rapi, fv1, fv2, z, lineWidth, gradHax);
}

static inline void debug_render_line(noeRAPI_t *rapi, polyReal_t *v1, polyReal_t *v2, float z = 0.0f, float lineWidth = 8.0f, float gradHax = 0.0f)
{
	float fv1[2] = { float(v1[0]), float(v1[1]) };
	float fv2[2] = { float(v2[0]), float(v2[1]) };
	debug_render_line(rapi, fv1, fv2, z, lineWidth, gradHax);
}

static inline void debug_render_point(noeRAPI_t *rapi, float *v1, float z = 0.0f, float pointSize = 12.0f)
{
	RichVec3 pos1(v1[0], v1[1], z);
	rapi->rpgBegin(RPGEO_QUAD_ABC_ACD);
	rapi->rpgVertex3f((pos1 + RichVec3(-pointSize, pointSize, 0.0f)).v);
	rapi->rpgVertex3f((pos1 + RichVec3(-pointSize, -pointSize, 0.0f)).v);
	rapi->rpgVertex3f((pos1 + RichVec3(pointSize, -pointSize, 0.0f)).v);
	rapi->rpgVertex3f((pos1 + RichVec3(pointSize, pointSize, 0.0f)).v);
	rapi->rpgEnd();
}

static inline void debug_render_point(noeRAPI_t *rapi, short *v1, float z = 0.0f, float pointSize = 12.0f)
{
	float fv1[2] = { float(v1[0]), float(v1[1]) };
	debug_render_point(rapi, fv1, z, pointSize);
}

static inline void debug_render_point(noeRAPI_t *rapi, polyReal_t *v1, float z = 0.0f, float pointSize = 12.0f)
{
	float fv1[2] = { float(v1[0]), float(v1[1]) };
	debug_render_point(rapi, fv1, z, pointSize);
}

static inline void debug_render_box(noeRAPI_t *rapi, short *box, float z = 0.0f)
{
	short v1[2];
	short v2[2];

	v1[0] = box[2];
	v1[1] = box[0];
	v2[0] = box[2];
	v2[1] = box[1];
	debug_render_line(rapi, v1, v2, z);
	v1[0] = box[3];
	v1[1] = box[0];
	v2[0] = box[3];
	v2[1] = box[1];
	debug_render_line(rapi, v1, v2, z);
	v1[0] = box[2];
	v1[1] = box[0];
	v2[0] = box[3];
	v2[1] = box[0];
	debug_render_line(rapi, v1, v2, z);
	v1[0] = box[2];
	v1[1] = box[1];
	v2[0] = box[3];
	v2[1] = box[1];
	debug_render_line(rapi, v1, v2, z);
}

static inline bool intersect_lines_2d(const segChopLine_t &l1, const segChopLine_t &l2, polyReal_t &frac, bool segTest = false)
{
	const polyReal_t x1 = l1.pos[0];
	const polyReal_t y1 = l1.pos[1];
	const polyReal_t x2 = l1.pos[0]+l1.length[0];
	const polyReal_t y2 = l1.pos[1]+l1.length[1];

	const polyReal_t x3 = l2.pos[0];
	const polyReal_t y3 = l2.pos[1];
	const polyReal_t x4 = l2.pos[0]+l2.length[0];
	const polyReal_t y4 = l2.pos[1]+l2.length[1];

	const polyReal_t d1 = (x2-x1)*(y4-y3);
	const polyReal_t d2 = (y2-y1)*(x4-x3);
	const polyReal_t d = d1-d2;
	if (d != 0.0)
	{
		frac = ( ( (y1-y3)*(x4-x3) ) - (x1-x3) * (y4-y3) ) / d;
		const polyReal_t otherFrac = ( ( (y1-y3)*(x2-x1) ) - (x1-x3) * (y2-y1) ) / d;
		if (!segTest || (frac >= 0.0 && frac < 1.0 && otherFrac >= 0.0 && otherFrac <= 1.0))
		{
			//pOut[0] = x1 + frac*(x2-x1);
			//pOut[1] = y1 + frac*(y2-y1);
			return true;
		}
	}
	return false;
}

static inline polyReal_t vec_dot_2d(const polyReal_t *v1, const polyReal_t *v2)
{
	return (v1[0]*v2[0] + v1[1]*v2[1]);
}

static inline polyReal_t vec_squarelen_2d(const polyReal_t *v)
{
	return (v[0]*v[0] + v[1]*v[1]);
}

static inline polyReal_t vec_normalize_2d(polyReal_t *v)
{
	const polyReal_t l = (polyReal_t)sqrt(vec_squarelen_2d(v));
	if (l != 0.0)
	{
		const polyReal_t invL = 1.0/l;
		v[0] *= invL;
		v[1] *= invL;
	}
	return l;
}

static inline polyReal_t get_line_angle_2d(const segChopLine_t &l1)
{
	polyReal_t dirNorm[2] = { l1.length[0], l1.length[1] };
	vec_normalize_2d(dirNorm);
	return (polyReal_t)atan2(dirNorm[0], dirNorm[1]);
}

static inline void set_convex_poly_from_bounds(noeRAPI_t *rapi, convexMapPoly_t *convexPoly, polyReal_t *mins, polyReal_t *maxs)
{
	if (convexPoly->numPointsAlloc < 4)
	{
		convexPoly->numPointsAlloc = 4;
		if (convexPoly->points)
		{
			rapi->Noesis_UnpooledFree(convexPoly->points);
		}
		convexPoly->points = (polyPoint_t *)rapi->Noesis_UnpooledAlloc(sizeof(polyPoint_t)*convexPoly->numPointsAlloc);
	}
	if (convexPoly->numEdgesAlloc < 4)
	{
		convexPoly->numEdgesAlloc = 4;
		if (convexPoly->edges)
		{
			rapi->Noesis_UnpooledFree(convexPoly->edges);
		}
		convexPoly->edges = (polyEdge_t *)rapi->Noesis_UnpooledAlloc(sizeof(polyEdge_t)*convexPoly->numEdgesAlloc);
	}

	convexPoly->numPoints = 4;
	convexPoly->numEdges = 4;
	convexPoly->points[0].p[0] = mins[0];
	convexPoly->points[0].p[1] = mins[1];
	convexPoly->points[1].p[0] = maxs[0];
	convexPoly->points[1].p[1] = mins[1];
	convexPoly->points[2].p[0] = maxs[0];
	convexPoly->points[2].p[1] = maxs[1];
	convexPoly->points[3].p[0] = mins[0];
	convexPoly->points[3].p[1] = maxs[1];
	convexPoly->edges[0].idx[0] = 0;
	convexPoly->edges[0].idx[1] = 1;
	convexPoly->edges[1].idx[0] = 1;
	convexPoly->edges[1].idx[1] = 2;
	convexPoly->edges[2].idx[0] = 2;
	convexPoly->edges[2].idx[1] = 3;
	convexPoly->edges[3].idx[0] = 3;
	convexPoly->edges[3].idx[1] = 0;
}

static inline void convex_poly_check_edge_alloc(noeRAPI_t *rapi, convexMapPoly_t *convexPoly, int newEdgeCount)
{
	if (newEdgeCount > convexPoly->numEdgesAlloc)
	{
		while (newEdgeCount > convexPoly->numEdgesAlloc)
		{
			convexPoly->numEdgesAlloc *= 2;
		}
		polyEdge_t *newEdges = (polyEdge_t *)rapi->Noesis_UnpooledAlloc(sizeof(polyEdge_t)*convexPoly->numEdgesAlloc);
		memcpy(newEdges, convexPoly->edges, sizeof(polyEdge_t)*convexPoly->numEdges);
		rapi->Noesis_UnpooledFree(convexPoly->edges);
		convexPoly->edges = newEdges;
	}
}

static inline void convex_poly_check_point_alloc(noeRAPI_t *rapi, convexMapPoly_t *convexPoly, int newPointCount)
{
	if (newPointCount > convexPoly->numPointsAlloc)
	{
		while (newPointCount > convexPoly->numPointsAlloc)
		{
			convexPoly->numPointsAlloc *= 2;
		}
		polyPoint_t *newPoints = (polyPoint_t *)rapi->Noesis_UnpooledAlloc(sizeof(polyPoint_t)*convexPoly->numPointsAlloc);
		memcpy(newPoints, convexPoly->points, sizeof(polyPoint_t)*convexPoly->numPoints);
		rapi->Noesis_UnpooledFree(convexPoly->points);
		convexPoly->points = newPoints;
	}
}

static inline void split_convex_poly_edge(noeRAPI_t *rapi, convexMapPoly_t *convexPoly, int edgeIndex, polyReal_t fraction)
{
	assert(convexPoly->edges && convexPoly->numEdges > 0);
	assert(convexPoly->points && convexPoly->numPoints > 0);

	int newEdgeCount = convexPoly->numEdges+1;
	int newPointCount = convexPoly->numPoints+1;
	convex_poly_check_edge_alloc(rapi, convexPoly, newEdgeCount);
	convex_poly_check_point_alloc(rapi, convexPoly, newPointCount);

	convexPoly->numEdges = newEdgeCount;
	convexPoly->numPoints = newPointCount;

	int newEdgeIndex = edgeIndex+1;
	int newPointIndex = newPointCount-1;

	if (newEdgeIndex < newEdgeCount-1)
	{
		//move the edges up, so we preserve winding order (not the fastest way to deal with this, but it's convenient)
		const int numToCopy = newEdgeCount-newEdgeIndex-1;
		memcpy(convexPoly->edges+newEdgeIndex+1, convexPoly->edges+newEdgeIndex, sizeof(polyEdge_t)*numToCopy);
	}
	polyEdge_t *edge = convexPoly->edges+edgeIndex;
	polyPoint_t *p0 = convexPoly->points+edge->idx[0];
	polyPoint_t *p1 = convexPoly->points+edge->idx[1];
	polyEdge_t *newEdge = convexPoly->edges+newEdgeIndex;
	polyPoint_t *newPoint = convexPoly->points+newPointIndex;

	//create a new point along the edge
	newPoint->p[0] = p0->p[0] + (p1->p[0]-p0->p[0])*fraction;
	newPoint->p[1] = p0->p[1] + (p1->p[1]-p0->p[1])*fraction;
	//make the old edge the first segment of the split edge, and the new edge the second segment
	newEdge->idx[0] = newPointIndex;
	newEdge->idx[1] = edge->idx[1];
	edge->idx[1] = newPointIndex;
}

static inline void set_chopline_for_polyedge(const convexMapPoly_t *convexPoly, int edgeIndex, segChopLine_t *edgeLine)
{
	polyEdge_t *edge = convexPoly->edges+edgeIndex;
	const polyReal_t *edgeP0 = convexPoly->points[edge->idx[0]].p;
	const polyReal_t *edgeP1 = convexPoly->points[edge->idx[1]].p;
	edgeLine->pos[0] = edgeP0[0];
	edgeLine->pos[1] = edgeP0[1];
	edgeLine->length[0] = edgeP1[0]-edgeP0[0];
	edgeLine->length[1] = edgeP1[1]-edgeP0[1];
}

static inline int get_side_of_point_on_line(const segChopLine_t *chopLine, const polyReal_t *point, polyReal_t eps = 0.0)
{
	polyReal_t pointDir[2] = { point[0]-chopLine->pos[0], point[1]-chopLine->pos[1] };
	polyReal_t lineDir[2] = { chopLine->length[1], -chopLine->length[0] };

	if (vec_normalize_2d(pointDir) <= eps)
	{
		return 0;
	}
	vec_normalize_2d(lineDir);

	polyReal_t pointSide = vec_dot_2d(pointDir, lineDir);
	if ((polyReal_t)fabs(pointSide) <= eps)
	{
		return 0;
	}
	return (pointSide < 0.0) ? -1 : 1;
}

static inline polyReal_t get_point_dist_from_line(const polyReal_t *point, const segChopLine_t *chopLine)
{
	const polyReal_t lineLenSq = vec_squarelen_2d(chopLine->length);
	const polyReal_t pointDir[2] = { point[0]-chopLine->pos[0], point[1]-chopLine->pos[1] };
	const polyReal_t frac = vec_dot_2d(pointDir, chopLine->length) / lineLenSq;
	//we don't care if it actually falls on the line segment, we just want to get distance
	//from the point projected on the line.
	const polyReal_t pointOnLine[2] = { chopLine->pos[0] + frac*chopLine->length[0], chopLine->pos[1] + frac*chopLine->length[1] };
	const polyReal_t pointOnLineToPoint[2] = { point[0]-pointOnLine[0], point[1]-pointOnLine[1] };

	return sqrt(vec_squarelen_2d(pointOnLineToPoint));
}

static inline polyReal_t get_point_dist_from_line_seg_sq(const polyReal_t *point, const polyReal_t *linePos, const polyReal_t *lineLen)
{
	const polyReal_t lineLenSq = vec_squarelen_2d(lineLen);
	polyReal_t pointDir[2] = { point[0]-linePos[0], point[1]-linePos[1] };
	const polyReal_t frac = vec_dot_2d(pointDir, lineLen) / lineLenSq;
	if (frac < 0.0)
	{
		return vec_squarelen_2d(pointDir);
	}
	else if (frac > 1.0)
	{
		pointDir[0] -= lineLen[0];
		pointDir[1] -= lineLen[1];
		return vec_squarelen_2d(pointDir);
	}
	//we don't care if it actually falls on the line segment, we just want to get distance
	//from the point projected on the line.
	const polyReal_t pointOnLine[2] = { linePos[0] + frac*lineLen[0], linePos[1] + frac*lineLen[1] };
	const polyReal_t pointOnLineToPoint[2] = { point[0]-pointOnLine[0], point[1]-pointOnLine[1] };

	return vec_squarelen_2d(pointOnLineToPoint);
}

static inline int chop_convex_poly(noeRAPI_t *rapi, convexMapPoly_t *convexPoly, segChopLine_t *chopLine, polyPoint_t *midPoint,
								   polyReal_t minLenToCut)
{
	const int maxHitEdges = 2;
	int hitEdges[maxHitEdges] = { -1, -1 };
	polyReal_t hitPositions[maxHitEdges][2];
	polyReal_t hitFracs[maxHitEdges];
	int hitEdgeCount = 0;
	int pointSide = get_side_of_point_on_line(chopLine, midPoint->p);
	if (pointSide == 0)
	{
		rapi->LogOutput("WARNING: Can't chop convex poly, midpoint is on the chop line!\n");
		return -1;
	}

	const polyReal_t planeSideEps = 0.00001;
	const polyReal_t overlapEps = 0.000001;

	if (minLenToCut > 0.0)
	{
		//don't bother cutting if there's no possibility we could take a sizeable chunk off
		polyReal_t bestPointDist = 0.0;
		for (int i = 0; i < convexPoly->numEdges; i++)
		{
			polyEdge_t *edge = convexPoly->edges+i;
			const polyReal_t *edgeP0 = convexPoly->points[edge->idx[0]].p;
			int edgeP0Side = get_side_of_point_on_line(chopLine, edgeP0, planeSideEps);
			if (edgeP0Side != 0 && edgeP0Side != pointSide)
			{
				//if it's not on the plane or on the right side of the chop line, see how far away it
				//is from the line.
				const polyReal_t distToChopLine = get_point_dist_from_line(edgeP0, chopLine);
				bestPointDist = (distToChopLine > bestPointDist) ? distToChopLine : bestPointDist;
			}
		}

		if (bestPointDist < minLenToCut)
		{
			return 0;
		}
	}

	for (int i = 0; i < convexPoly->numEdges; i++)
	{
		segChopLine_t edgeLine;
		set_chopline_for_polyedge(convexPoly, i, &edgeLine);

		polyReal_t intersectionFrac;
		if (intersect_lines_2d(edgeLine, *chopLine, intersectionFrac) &&
			intersectionFrac >= 0.0 && intersectionFrac < 1.0)
		{
			//< 1 instead of <=, because we want to catch anything perfectly intersecting a vertex on the
			//start of an edge instead of the end.
			const polyReal_t hitPos[2] = { edgeLine.pos[0] + edgeLine.length[0]*intersectionFrac, edgeLine.pos[1] + edgeLine.length[1]*intersectionFrac };
			if (hitEdgeCount == maxHitEdges)
			{
				//see if this intersection is better than the current one
				const polyReal_t curDif[2] = { hitPositions[maxHitEdges-1][0]-hitPositions[0][0], hitPositions[maxHitEdges-1][1]-hitPositions[0][1] };
				const polyReal_t newDif[2] = { hitPos[0]-hitPositions[0][0], hitPos[1]-hitPositions[0][1] };
				if (vec_squarelen_2d(newDif) > vec_squarelen_2d(curDif))
				{
					//it's better, replace the last hit with this one
					hitEdgeCount--;
				}
			}

			if (hitEdgeCount < maxHitEdges)
			{
				hitEdges[hitEdgeCount] = i;
				hitPositions[hitEdgeCount][0] = hitPos[0];
				hitPositions[hitEdgeCount][1] = hitPos[1];
				hitFracs[hitEdgeCount] = intersectionFrac;
				hitEdgeCount++;
			}
		}
	}

	if (hitEdgeCount == maxHitEdges)
	{
		if ((hitFracs[0] < overlapEps || 1.0-hitFracs[0] <= overlapEps) &&
			(hitFracs[1] < overlapEps || 1.0-hitFracs[1] <= overlapEps))
		{
			//we're pretty much directly overlapping an existing edge, so don't do anything.
			return 0;
		}

		for (int i = 0; i < hitEdgeCount; i++)
		{
			if (hitFracs[i] != 0.0)
			{
				//don't actually need to split if we're on the tip of the segment.
				//warning: this call may invalidate pointers to convex poly data due to reallocation.
				const int hitEdgeIndex = hitEdges[i];
				split_convex_poly_edge(rapi, convexPoly, hitEdgeIndex, hitFracs[i]);
				//offset indices to account for new edge
				for (int j = 0; j < hitEdgeCount; j++)
				{
					if (hitEdges[j] >= hitEdgeIndex)
					{
						hitEdges[j]++;
					}
				}
			}
		}
		//since we keep consistent winding in the edge list, all we need to do is point
		//the second edge back at the first edge. then we can run through and chop any
		//edge off which has a point on the wrong side of the plane.
		polyEdge_t *firstEdge = convexPoly->edges+hitEdges[1];
		polyEdge_t *secondEdge = convexPoly->edges+hitEdges[0];
		int firstEdgeEndSide = get_side_of_point_on_line(chopLine, convexPoly->points[firstEdge->idx[1]].p);
		if (firstEdgeEndSide != 0 && firstEdgeEndSide != pointSide)
		{
			firstEdge->idx[1] = secondEdge->idx[0];
		}
		else
		{
			secondEdge->idx[1] = firstEdge->idx[0];
		}
		for (int i = 0; i < convexPoly->numEdges; i++)
		{
			polyEdge_t *edge = convexPoly->edges+i;
			const polyReal_t *edgeP0 = convexPoly->points[edge->idx[0]].p;
			const polyReal_t *edgeP1 = convexPoly->points[edge->idx[1]].p;
			int edgeP0Side = get_side_of_point_on_line(chopLine, edgeP0, planeSideEps);
			int edgeP1Side = get_side_of_point_on_line(chopLine, edgeP1, planeSideEps);
			edgeP0Side = (edgeP0Side == 0) ? pointSide : edgeP0Side;
			edgeP1Side = (edgeP1Side == 0) ? pointSide : edgeP1Side;
			if (edgeP0Side != pointSide || edgeP1Side != pointSide)
			{
				//at least one of the points on the edge is on the wrong side, so cut the
				//edge off.
				if (convexPoly->numEdges <= 3)
				{
					rapi->LogOutput("WARNING: Tried to make convex poly non-convex!\n");
					return -1;
				}
				if (i < convexPoly->numEdges-1)
				{
					//we don't bother removing points from the list, so there's no need to remap.
					memcpy(edge, convexPoly->edges+i+1, sizeof(polyEdge_t)*(convexPoly->numEdges-i-1));
				}
				convexPoly->numEdges--;
				i--;
			}
		}
	}
	return hitEdgeCount;
}

static inline void free_convex_poly(noeRAPI_t *rapi, convexMapPoly_t *convexPoly)
{
	if (convexPoly->points)
	{
		rapi->Noesis_UnpooledFree(convexPoly->points);
	}
	if (convexPoly->edges)
	{
		rapi->Noesis_UnpooledFree(convexPoly->edges);
	}
	memset(convexPoly, 0, sizeof(convexMapPoly_t));
}

static inline void decode_glbsp_vert(const glbspVert_t *vert, polyReal_t *dst)
{
	dst[0] = polyReal_t(vert->xWhole) + polyReal_t(vert->xFrac)/65535.0;
	dst[1] = polyReal_t(vert->yWhole) + polyReal_t(vert->yFrac)/65535.0;
}

static inline void set_color_for_sector_light(noeRAPI_t *rapi, memLump_t &colorMapLump, mUShort_t lightLevel)
{
	float l = float(lightLevel) / 255.0f;
	convenient_set_color(rapi, l, l, l);
}

static inline BYTE *apply_color_palette(noeRAPI_t *rapi, BYTE *pixelData, BYTE *palData, int width, int height)
{
	BYTE *colorData = (BYTE *)rapi->Noesis_UnpooledAlloc(width*height*4);
	for (int i = 0; i < width*height; i++)
	{
		BYTE pix = pixelData[i];
		BYTE *color = palData + pix*3;
		BYTE *dst = colorData + i*4;
		dst[0] = color[0];
		dst[1] = color[1];
		dst[2] = color[2];
		dst[3] = 255;
	}
	return colorData;
}

static inline bool should_render_linedef_area(const char *texName)
{
	if (texName[0] != '-' || texName[1] != 0)
	{
		if (_strnicmp(texName, "AASTINKY", 8) != 0 && _strnicmp(texName, "AASHITTY", 8) != 0)
		{
			return true;
		}
	}
	return false;
}

static void render_linedef_portion(noeRAPI_t *rapi, doomMapRes_t &mr, const char *wallTexId, mapSideDef_t *sideDef, mapSector_t *sector,
								   mapSector_t *otherSector, mapLineDef_t *lineDef, int sdIndex, mapVert_t *v1, mapVert_t *v2,
								   float zBottom, float zTop, bool backWind, int pegType)
{
	int resIndex = mr.wallTexHash.GetResourceIndexForId(wallTexId);
	noesisTex_t *noeTex = NULL;
	if (resIndex >= 0)
	{
		noesisMaterial_t *noeMat = mr.noeMaterials[resIndex];
		rapi->rpgSetMaterial(noeMat->name);
		noeTex = mr.noeTextures[resIndex];
	}
	else
	{
		rapi->rpgSetMaterial("unknown");
	}

	float verts[4][3] =
	{
		{ float(v1->pos[0]), float(v1->pos[1]), zBottom },
		{ float(v1->pos[0]), float(v1->pos[1]), zTop },
		{ float(v2->pos[0]), float(v2->pos[1]), zTop },
		{ float(v2->pos[0]), float(v2->pos[1]), zBottom }
	};

	//combine with triangle picker plugin for convenient debug info in data viewer on click
	//char info[256];
	//const char *partString = (wallTexId == sideDef->lowerTex) ? "l" : (wallTexId == sideDef->upperTex) ? "u" : "m";
	//sprintf(info, "side_%04i_%s_%i_%i_%i_%i_%04x_%.02f_%.02f_%i", sdIndex, partString, sideDef->yOfs, sideDef->xOfs, pegType,
	//	lineDef->specialType, lineDef->flags, zBottom, zTop, (noeTex) ? noeTex->h : 0);
	//rapi->rpgSetName(info);
	
	float uvs[4][2];
	if (noeTex)
	{
		//what a mess. see http://doom.wikia.com/wiki/Texture_alignment
		const float surfHeight = fabsf(zTop-zBottom);
		const float lineDir[2] = { verts[0][0]-verts[3][0], verts[0][1]-verts[3][1] };
		const float surfWidth = sqrtf(lineDir[0]*lineDir[0] + lineDir[1]*lineDir[1]);

		float textureTop = 0.0f;
		if (wallTexId == sideDef->middleTex || !otherSector)
		{
			assert(pegType != 1 && pegType != 2);
			switch (pegType)
			{
			case 3:
				textureTop = zBottom+float(noeTex->h);
				break;
			default:
				textureTop = (!otherSector) ? float(sector->ceilingHeight) : float(sector->floorHeight);
				break;
			}
		}
		else
		{
			assert(pegType != 3);
			const float highestCeiling = g_mfn->Math_Max2(float(sector->ceilingHeight), float(otherSector->ceilingHeight));
			const float lowestCeiling = g_mfn->Math_Min2(float(sector->ceilingHeight), float(otherSector->ceilingHeight));
			const float highestFloor = g_mfn->Math_Max2(float(sector->floorHeight), float(otherSector->floorHeight));
			const float lowestFloor = g_mfn->Math_Min2(float(sector->floorHeight), float(otherSector->floorHeight));

			switch (pegType)
			{
			case 1:
				//textureTop = lowestFloor+float(noeTex->h);
				//this is what the wiki describes, but this seems to be the correct behavior:
				textureTop = float(sector->ceilingHeight);
				break;
			case 2:
				textureTop = highestCeiling;
				break;
			default:
				if (wallTexId == sideDef->upperTex)
				{
					textureTop = lowestCeiling+float(noeTex->h);
				}
				else
				{
					textureTop = highestFloor;
				}
				break;
			}
		}

		const float startVOfs = textureTop-zTop;
		const float startU = float(sideDef->xOfs)/float(noeTex->w);
		const float startV = (float(sideDef->yOfs)+startVOfs)/float(noeTex->h);
		const float endU = (backWind) ? startU + surfWidth/float(noeTex->w) : startU - surfWidth/float(noeTex->w);
		const float endV = startV + surfHeight/float(noeTex->h);

		uvs[0][0] = startU;
		uvs[0][1] = endV;
		uvs[1][0] = startU;
		uvs[1][1] = startV;
		uvs[2][0] = endU;
		uvs[2][1] = startV;
		uvs[3][0] = endU;
		uvs[3][1] = endV;
	}
	else
	{
		memset(uvs, 0, sizeof(uvs));
	}

	rapi->rpgBegin(RPGEO_POLYGON);

	if (backWind)
	{
		rapi->rpgVertUV2f(uvs[3], 0);
		rapi->rpgVertex3f(verts[3]);
		rapi->rpgVertUV2f(uvs[2], 0);
		rapi->rpgVertex3f(verts[2]);
		rapi->rpgVertUV2f(uvs[1], 0);
		rapi->rpgVertex3f(verts[1]);
		rapi->rpgVertUV2f(uvs[0], 0);
		rapi->rpgVertex3f(verts[0]);
	}
	else
	{
		rapi->rpgVertUV2f(uvs[0], 0);
		rapi->rpgVertex3f(verts[0]);
		rapi->rpgVertUV2f(uvs[1], 0);
		rapi->rpgVertex3f(verts[1]);
		rapi->rpgVertUV2f(uvs[2], 0);
		rapi->rpgVertex3f(verts[2]);
		rapi->rpgVertUV2f(uvs[3], 0);
		rapi->rpgVertex3f(verts[3]);
	}

	rapi->rpgEnd();
}

//get a lump for a specific map
static wadLump_t *Model_DoomWad_GetMapLump(memLump_t &mapBase, char *lumpName)
{
	wadLump_t *lumps = (wadLump_t *)((BYTE *)mapBase.base + mapBase.base->lumpsOfs);
	for (int i = mapBase.lIdx; i < mapBase.base->numLumps; i++)
	{
		wadLump_t *l = lumps+i;
		if (!memcmp(l->name, lumpName, 8))
		{
			return l;
		}
	}
	return NULL;
}

//is it this format?
bool Model_DoomWad_Check(BYTE *fileBuffer, int bufferLen, noeRAPI_t *rapi)
{
	if (bufferLen < sizeof(wadHdr_t))
	{
		return false;
	}
	wadHdr_t *hdr = (wadHdr_t *)fileBuffer;
	if (memcmp(hdr->id, "PWAD", 4) && memcmp(hdr->id, "IWAD", 4))
	{
		return false;
	}
	if (hdr->numLumps <= 0 || hdr->lumpsOfs <= 0 || hdr->lumpsOfs >= bufferLen)
	{
		return false;
	}
	int lumpEnd = hdr->lumpsOfs + sizeof(wadLump_t)*hdr->numLumps;
	if (lumpEnd <= 0 || lumpEnd > bufferLen)
	{
		return false;
	}
	return true;
}

//generate polygons directly from gl subsectors
static extraSubSectData_t *Model_DoomWad_TranslateGLSubSectors(
												mapLineDef_t *lineDefs, int numLineDefs, mapSideDef_t *sideDefs, int numSideDefs,
												mapVert_t *verts, int numVerts, glbspVert_t *glVerts, int numGLVerts,
												glbspSeg_t *glSegs, int numGLSegs, glbspSubSect_t *glSubSects, int numGLSubSects,
												LocalMemPool &localPool, noeRAPI_t *rapi)
{
	extraSubSectData_t *extraSS = (extraSubSectData_t *)localPool.Alloc(sizeof(extraSubSectData_t)*numGLSubSects);
	for (int i = 0; i < numGLSubSects; i++)
	{
		extraSubSectData_t *ess = extraSS+i;
		ess->nodeParent = -1; //don't care on this path

		const glbspSubSect_t *glSS = glSubSects+i;
		unsigned int firstSegIndex = 0;
		glbspSeg_t *firstSeg = glSegs+glSS->firstSeg;
		while (firstSeg->lineDef == 0xFFFF && firstSegIndex < glSS->segNum-1)
		{
			firstSegIndex++;
			firstSeg = glSegs+glSS->firstSeg+firstSegIndex;
		}
		if (firstSeg->lineDef == 0xFFFF)
		{
			rapi->LogOutput("WARNING: Nothing but minisegs on subsector %i.\n", i);
			continue;
		}

		const mapLineDef_t *lineDef = lineDefs+firstSeg->lineDef;
		const int sideDefIndex = (firstSeg->side == 0) ? lineDef->rightSideDef : lineDef->leftSideDef;
		if (sideDefIndex == 0xFFFF)
		{
			rapi->LogOutput("WARNING: Could not get sector for subsector %i.\n", i);
			continue;
		}
		const mapSideDef_t *sideDef = sideDefs+sideDefIndex;
		ess->sectorIndex = sideDef->sectorNum;

		ess->numPoints = glSS->segNum;
		ess->convexPoints = (polyPoint_t *)localPool.Alloc(sizeof(polyPoint_t)*glSS->segNum);
		for (unsigned int j = 0; j < glSS->segNum; j++)
		{
			const glbspSeg_t *seg = glSegs+glSS->firstSeg+j;
			polyPoint_t *dstPos = ess->convexPoints+(glSS->segNum-1-j);
			int vertIndex = (seg->startVert & 0x3FFFFFFF);
			if ((seg->startVert & 0xC0000000))
			{
				assert(vertIndex < numGLVerts);
				//it's a gl vert
				const glbspVert_t *vert = glVerts+vertIndex;
				decode_glbsp_vert(vert, dstPos->p);
			}
			else
			{
				assert(vertIndex < numVerts);
				const mapVert_t *vert = verts+vertIndex;
				dstPos->p[0] = polyReal_t(vert->pos[0]);
				dstPos->p[1] = polyReal_t(vert->pos[1]);
			}
		}
	}

	return extraSS;
}

//this works lovely on doom1, but in doom2 the node builder starts throwing in all kinds of non-convex subsectors that
//this routine does not deal with at all. after throwing some ideas around on how to deal with them myself, i decided
//it's not worth doing the work of rebuilding subsectors and just added glbsp support.
static extraSubSectData_t *Model_DoomWad_CreateConvexSubsectorPolygons(
											mapLineDef_t *lineDefs, int numLineDefs, mapSideDef_t *sideDefs, int numSideDefs,
											mapVert_t *verts, int numVerts, mapSector_t *sectors, int numSectors,
											mapSubSector_t *subSectors, int numSubSectors, mapSeg_t *segs, int numSegs,
											mapNode_t *nodes, int numNodes, LocalMemPool &localPool, noeRAPI_t *rapi
											)
{
	extraSubSectData_t *extraSS = (extraSubSectData_t *)localPool.Alloc(sizeof(extraSubSectData_t)*numSubSectors);
	extraNodeData_t *extraNodes = (extraNodeData_t *)localPool.Alloc(sizeof(extraNodeData_t)*numNodes);
	memset(extraSS, 0, sizeof(extraSubSectData_t)*numSubSectors);
	memset(extraNodes, 0, sizeof(extraNodeData_t)*numNodes);
	for (int i = 0; i < numSubSectors; i++)
	{
		extraSS[i].nodeParent = -1;
	}
	for (int i = 0; i < numNodes; i++)
	{
		extraNodes[i].parentIndex = -1;
	}

#if RECOVER_NODE_PARTITION_PRECISION != 0
	CArrayList<const mapLineDef_t *> nodeLineCandidates;
#endif
	for (int i = 0; i < numNodes; i++)
	{
		const mapNode_t *node = nodes+i;
		for (int j = 0; j < 2; j++)
		{
			if (node->children[j] & 0x8000)
			{
				int ssIndex = (node->children[j] & 0x7FFF);
				extraSubSectData_t *ess = extraSS+ssIndex;
				assert(ess->nodeParent == -1);
				ess->nodeParent = i;
			}
			else
			{
				extraNodeData_t *childEN = extraNodes+node->children[j];
				assert(childEN->parentIndex == -1);
				childEN->parentIndex = i;
			}
		}

		extraNodeData_t *en = extraNodes+i;
		en->partLine[0] = polyReal_t(node->partLine[0]);
		en->partLine[1] = polyReal_t(node->partLine[1]);
		en->partLineLen[0] = polyReal_t(node->partLineLen[0]);
		en->partLineLen[1] = polyReal_t(node->partLineLen[1]);
#if RECOVER_NODE_PARTITION_PRECISION == 1
		for (int j = 0; j < numLineDefs; j++)
		{
			const mapLineDef_t *lineDef = lineDefs+j;
			const mapVert_t *v1 = verts+lineDef->startVert;
			const mapVert_t *v2 = verts+lineDef->endVert;
			if ((v1->pos[0] == node->partLine[0] && v1->pos[1] == node->partLine[1]) ||
				(v2->pos[0] == node->partLine[0] && v2->pos[1] == node->partLine[1]))
			{
				nodeLineCandidates.Append(lineDef);
			}
		}
#elif RECOVER_NODE_PARTITION_PRECISION == 2
		//we don't even need to care if the line actually starts in the same place. just try to find
		//a segment that it's actually on or near, then we'll see if the direction if close enough.
		for (int j = 0; j < numLineDefs; j++)
		{
			const mapLineDef_t *lineDef = lineDefs+j;
			const mapVert_t *v1 = verts+lineDef->startVert;
			const mapVert_t *v2 = verts+lineDef->endVert;

			const polyReal_t pos[2] = { polyReal_t(v1->pos[0]), polyReal_t(v1->pos[1]) };
			const polyReal_t dir[2] = { polyReal_t(v2->pos[0])-pos[0], polyReal_t(v2->pos[1])-pos[1] };

			const polyReal_t lineDistSq = get_point_dist_from_line_seg_sq(en->partLine, pos, dir);
			if (lineDistSq < 1.0)
			{
				nodeLineCandidates.Append(lineDef);
			}
		}
#endif

#if RECOVER_NODE_PARTITION_PRECISION != 0
		if (nodeLineCandidates.Num() > 0)
		{
			polyReal_t normalizedLineDir[2] = { en->partLineLen[0], en->partLineLen[1] };
			vec_normalize_2d(normalizedLineDir);
			int bestCandidate = -1;
			polyReal_t bestDir[2];
			polyReal_t bestDif = 0.9; //don't use anything less than 0.9
			for (int j = 0; j < nodeLineCandidates.Num(); j++)
			{
				const mapLineDef_t *lineDef = nodeLineCandidates[j];
				const mapVert_t *v1 = verts+lineDef->startVert;
				const mapVert_t *v2 = verts+lineDef->endVert;
				polyReal_t dir[2] = { polyReal_t(v2->pos[0])-polyReal_t(v1->pos[0]), polyReal_t(v2->pos[1])-polyReal_t(v1->pos[1]) };
				polyReal_t nDir[2] = { dir[0], dir[1] };
				vec_normalize_2d(nDir);
				//we don't actually care if length is similar, we only need directionality
				polyReal_t dDot = vec_dot_2d(normalizedLineDir, nDir);
				if (dDot < 0.0)
				{
					dDot = -dDot;
					dir[0] = -dir[0];
					dir[1] = -dir[1];
				}
				if (dDot > bestDif)
				{
					bestCandidate = j;
					bestDir[0] = dir[0];
					bestDir[1] = dir[1];
					bestDif = dDot;
				}
			}
			if (bestCandidate != -1)
			{
				en->partLineLen[0] = bestDir[0];
				en->partLineLen[1] = bestDir[1];
			}
			nodeLineCandidates.Reset();
		}
		/*
		else
		{
			polyReal_t ex[2] = {en->partLine[0]+en->partLineLen[0], en->partLine[1]+en->partLineLen[1]};
			rapi->rpgSetName("CrappyLines");
			debug_render_line(rapi, en->partLine, ex, 32.0f, 16.0f, 0.1f);
			rapi->rpgSetName(NULL);
		}
		*/
#endif
	}

	polyReal_t mapMins[2], mapMaxs[2];
	mapMins[0] = mapMaxs[0] = polyReal_t(verts->pos[0]);
	mapMins[1] = mapMaxs[1] = polyReal_t(verts->pos[1]);
	for (int i = 1; i < numVerts; i++)
	{
		mapVert_t *v = verts+i;
		polyReal_t pos[2] = { polyReal_t(v->pos[0]), polyReal_t(v->pos[1]) };
		mapMins[0] = (pos[0] < mapMins[0]) ? pos[0] : mapMins[0];
		mapMins[1] = (pos[1] < mapMins[1]) ? pos[1] : mapMins[1];
		mapMaxs[0] = (pos[0] > mapMaxs[0]) ? pos[0] : mapMaxs[0];
		mapMaxs[1] = (pos[1] > mapMaxs[1]) ? pos[1] : mapMaxs[1];
	}

	convexMapPoly_t convexPoly;
	memset(&convexPoly, 0, sizeof(convexMapPoly_t));

	for (int i = 0; i < numSubSectors; i++)
	{
		extraSubSectData_t *ess = extraSS+i;
		const mapSubSector_t *ss = subSectors+i;

		if (ess->nodeParent < 0)
		{
			continue;
		}

		assert(ss->segNum > 0);
		set_convex_poly_from_bounds(rapi, &convexPoly, mapMins, mapMaxs);

		polyPoint_t midPoint;
		const mapSeg_t *firstSeg = segs+ss->firstSeg;
		const mapVert_t *segV1 = verts+firstSeg->startVert;
		const mapVert_t *segV2 = verts+firstSeg->endVert;
		const polyReal_t segPos[2] = { polyReal_t(segV1->pos[0]), polyReal_t(segV1->pos[1]) };
		polyReal_t segDir[2] = { polyReal_t(segV2->pos[0])-segPos[0], polyReal_t(segV2->pos[1])-segPos[1] };

		midPoint.p[0] = polyReal_t(segV1->pos[0]) + segDir[0]*0.5;
		midPoint.p[1] = polyReal_t(segV1->pos[1]) + segDir[1]*0.5;
		vec_normalize_2d(segDir);
		const polyReal_t segRight[2] = { segDir[1], -segDir[0] };
		//this is a little dangerous, line precision can end up chopping the sector down to nothing.
		midPoint.p[0] += segRight[0]*0.9;
		midPoint.p[1] += segRight[1]*0.9;
		/*
		debug_render_line(rapi, segV1->pos, segV2->pos, 32.0f, 16.f, 0.1f);
		polyReal_t test[2] = { midPoint.p[0] + segRight[0]*12.0f, midPoint.p[1] + segRight[1]*12.0f };
		debug_render_point(rapi, test, 32.0f, 24.0f);
		*/

		const mapLineDef_t *lineDef = lineDefs+firstSeg->lineDef;
		const int sideDefIndex = (firstSeg->side == 0) ? lineDef->rightSideDef : lineDef->leftSideDef;
		if (sideDefIndex == 0xFFFF)
		{
			rapi->LogOutput("WARNING: Could not get sector for subsector %i.\n", i);
			continue;
		}
		mapSideDef_t *sideDef = sideDefs+sideDefIndex;
		//mapSector_t *sector = sectors+sideDef->sectorNum;
		ess->sectorIndex = sideDef->sectorNum;

		//chop the convex poly with all of the parent node planes
		int parentNode = ess->nodeParent;
		while (parentNode >= 0)
		{
			const mapNode_t *node = nodes+parentNode;
			const extraNodeData_t *en = extraNodes+parentNode;
			parentNode = en->parentIndex;

			segChopLine_t chopLine;
			chopLine.pos[0] = polyReal_t(en->partLine[0]);
			chopLine.pos[1] = polyReal_t(en->partLine[1]);
			chopLine.length[0] = polyReal_t(en->partLineLen[0]);
			chopLine.length[1] = polyReal_t(en->partLineLen[1]);
			chop_convex_poly(rapi, &convexPoly, &chopLine, &midPoint, 0.0);
		}
		//now chop it with the subsector line segments
		for (int j = 0; j < ss->segNum; j++)
		{
			const mapSeg_t *seg = segs+ss->firstSeg+j;
			const mapLineDef_t *lineDef = lineDefs+seg->lineDef;
			const mapVert_t *v1 = verts+lineDef->startVert;
			const mapVert_t *v2 = verts+lineDef->endVert;

			segChopLine_t chopLine;
			chopLine.pos[0] = polyReal_t(v1->pos[0]);
			chopLine.pos[1] = polyReal_t(v1->pos[1]);
			chopLine.length[0] = polyReal_t(v2->pos[0])-polyReal_t(v1->pos[0]);
			chopLine.length[1] = polyReal_t(v2->pos[1])-polyReal_t(v1->pos[1]);
			//typically, once we get to the subsector segments, the damage has been done. so we don't want to
			//cut into the subsector even more unless it's going to take a significant amount of geometry off,
			//otherwise we're likely to just produce ugly slivers due to imprecision and edges not lining up
			//between node planes and segments. so we use a default min cut distance of 8.
			//(note - i've bumped this from 2 to 16 because excessive imprecision in segs causes a lot of slices
			//through subsectors otherwise. this is a shitty solution.)
			const polyReal_t segCutMin = (g_opts->minSecCutDist != 0.0) ? g_opts->minSecCutDist : 16.0;
			chop_convex_poly(rapi, &convexPoly, &chopLine, &midPoint, segCutMin);
		}

		if (convexPoly.numEdges >= 3)
		{
			ess->numPoints = 0;
			ess->convexPoints = (polyPoint_t *)localPool.Alloc(sizeof(polyPoint_t)*convexPoly.numEdges);
			for (int j = 0; j < convexPoly.numEdges; j++)
			{
				const polyEdge_t *edge = convexPoly.edges+j;

				if (g_opts->collapseEdges != 0.0)
				{
					//check for edge collapsing
					const polyReal_t collapseEps = g_opts->collapseEdges;
					const unsigned int lastEdgeIndex = (((unsigned int)j)-1)%convexPoly.numEdges;
					const polyEdge_t *lastEdge = convexPoly.edges+lastEdgeIndex;
					if (lastEdge->idx[1] == edge->idx[0])
					{
						polyPoint_t *p1 = convexPoly.points+edge->idx[0];
						polyPoint_t *p2 = convexPoly.points+edge->idx[1];
						polyReal_t edgeDir[2] = { p2->p[0]-p1->p[0], p2->p[1]-p1->p[1] };
						polyPoint_t *lastP1 = convexPoly.points+lastEdge->idx[0];
						polyPoint_t *lastP2 = convexPoly.points+lastEdge->idx[1];
						polyReal_t lastEdgeDir[2] = { lastP2->p[0]-lastP1->p[0], lastP2->p[1]-lastP1->p[1] };
						if (vec_normalize_2d(edgeDir) <= (1.0-collapseEps))
						{
							//this is a degenerate segment
							continue;
						}
						if (vec_normalize_2d(lastEdgeDir) > (1.0-collapseEps))
						{
							polyReal_t dp = vec_dot_2d(edgeDir, lastEdgeDir);
							if (dp >= collapseEps)
							{
								//the edge can be collapsed.
								continue;
							}
						}
					}
				}

				const polyPoint_t *point = convexPoly.points+edge->idx[0];
				ess->convexPoints[ess->numPoints++] = *point;
				//useful for debugging if a certain subsector is screwing up
				/*
				if (i == 241)
				{
					float clrs[6][4] = {
						{1.0f, 0.0f, 0.0f, 1.0f},
						{0.0f, 1.0f, 0.0f, 1.0f},
						{0.0f, 0.0f, 1.0f, 1.0f},
						{0.0f, 1.0f, 1.0f, 1.0f},
						{1.0f, 1.0f, 1.0f, 1.0f},
						{0.0f, 0.0f, 0.0f, 1.0f},
					};
					rapi->rpgVertColor4f(clrs[j%6]);
					debug_render_point(rapi, point->p, 32.0f + float(j)*32.0f, 32.0f);
				}
				*/
			}
		}
		else
		{
			rapi->LogOutput("WARNING: Subsector %i has no convex polygon geometry.\n", i);
		}
	}

	free_convex_poly(rapi, &convexPoly);

	return extraSS;
}

//load a single map model
static noesisModel_t *Model_DoomWad_LoadMap(memLump_t &ml, wadLoad_t &wl, doomMapRes_t &mr, noeRAPI_t *rapi)
{
	wadLump_t *lineDefsL = Model_DoomWad_GetMapLump(ml, "LINEDEFS");
	wadLump_t *sideDefsL = Model_DoomWad_GetMapLump(ml, "SIDEDEFS");
	wadLump_t *vertexesL = Model_DoomWad_GetMapLump(ml, "VERTEXES");
	wadLump_t *segsL = Model_DoomWad_GetMapLump(ml, "SEGS\0\0\0\0");
	wadLump_t *subSectorsL = Model_DoomWad_GetMapLump(ml, "SSECTORS");
	wadLump_t *nodesL = Model_DoomWad_GetMapLump(ml, "NODES\0\0\0");
	wadLump_t *sectorsL = Model_DoomWad_GetMapLump(ml, "SECTORS\0");
	wadLump_t *behaviorL = Model_DoomWad_GetMapLump(ml, "BEHAVIOR");
	if (!lineDefsL || !sideDefsL || !vertexesL || !segsL || !subSectorsL || !nodesL || !sectorsL)
	{
		return NULL;
	}
	const int lineDefInFileSize = (behaviorL) ? sizeof(hexenLineDef_t) : sizeof(mapLineDef_t);
	BYTE *base = (BYTE *)ml.base;
	mapLineDef_t *lineDefs = (mapLineDef_t *)(base + lineDefsL->ofs);
	int numLineDefs = (lineDefsL->size / lineDefInFileSize);
	mapSideDef_t *sideDefs = (mapSideDef_t *)(base + sideDefsL->ofs);
	int numSideDefs = (sideDefsL->size / sizeof(mapSideDef_t));
	mapVert_t *verts = (mapVert_t *)(base + vertexesL->ofs);
	int numVerts = (vertexesL->size / sizeof(mapVert_t));
	mapSector_t *sectors = (mapSector_t *)(base + sectorsL->ofs);
	int numSectors = (sectorsL->size / sizeof(mapSector_t));
	mapSubSector_t *subSectors = (mapSubSector_t *)(base + subSectorsL->ofs);
	int numSubSectors = (subSectorsL->size / sizeof(mapSubSector_t));
	mapSeg_t *segs = (mapSeg_t *)(base + segsL->ofs);
	int numSegs = (segsL->size / sizeof(mapSeg_t));
	mapNode_t *nodes = (mapNode_t *)(base + nodesL->ofs);
	int numNodes = (nodesL->size / sizeof(mapNode_t));
	if (numLineDefs <= 0 || numSideDefs <= 0 || numVerts <= 0 || numSectors <= 0 || numSubSectors <= 0 || numSegs <= 0 || numNodes <= 0)
	{
		return NULL;
	}

	LocalMemPool localPool;

	if (behaviorL)
	{
		//hexen hack, just convert the linedefs
		hexenLineDef_t *hexenLineDefs = (hexenLineDef_t *)lineDefs;
		lineDefs = (mapLineDef_t *)localPool.Alloc(sizeof(mapLineDef_t)*numLineDefs);
		for (int i = 0; i < numLineDefs; i++)
		{
			const hexenLineDef_t *hld = hexenLineDefs+i;
			mapLineDef_t *ld = lineDefs+i;
			ld->startVert = hld->startVert;
			ld->endVert = hld->endVert;
			ld->flags = hld->flags;
			ld->specialType = 0;
			ld->sectorTag = 0;
			ld->rightSideDef = hld->rightSideDef;
			ld->leftSideDef = hld->leftSideDef;
		}
	}

	glbspVert_t *glVerts = NULL;
	int numGLVerts = 0;
	glbspSeg_t *glSegs = NULL;
	int numGLSegs = 0;
	glbspSubSect_t *glSubSects = NULL;
	int numGLSubSects = 0;
	int glVer = -1;
	if (!g_opts->disableGLBSP)
	{
		int glMLIndex = -1;
		//search for gl lump
		for (int i = 0; i < wl.glLumps.Num(); i++)
		{
			if (!_strnicmp(ml.l->name, &wl.glLumps[i].l->name[3], 5))
			{
				glMLIndex = i;
				break;
			}
		}
		if (glMLIndex != -1)
		{
			memLump_t &glML = wl.glLumps[glMLIndex];
			wadLump_t *glVertsLump = Model_DoomWad_GetMapLump(glML, "GL_VERT");
			wadLump_t *glSegsLump = Model_DoomWad_GetMapLump(glML, "GL_SEGS");
			wadLump_t *glSubSectLump = Model_DoomWad_GetMapLump(glML, "GL_SSECT");
			//(if we've already got properly-convex gl subsectors, we don't need to even care about nodes)
			if (glVertsLump && glSegsLump && glSubSectLump)
			{
				BYTE *glVertsData = (BYTE *)glML.base + glVertsLump->ofs;
				BYTE *glSegsData = (BYTE *)glML.base + glSegsLump->ofs;
				BYTE *glSubSectData = (BYTE *)glML.base + glSubSectLump->ofs;
				if (!memcmp(glVertsData, "gNd2", 4))
				{
					//christ, who thought this was a good idea?
					glVer = (memcmp(glSegsData, "gNd3", 4) == 0 && memcmp(glSubSectData, "gNd3", 4) == 0) ? 3 : 2;
				}
				else if (!memcmp(glVertsData, "gNd5", 4))
				{
					glVer = 5;
				}
				else
				{
					rapi->LogOutput("WARNING: Unsupported glbsp version, ignoring GL lumps.\n");
				}

				if (glVer >= 0)
				{
					//no need to convert verts, they're the same in all supported versions.
					glVerts = (glbspVert_t *)(glVertsData+4);
					numGLVerts = (glVertsLump->size-4)/sizeof(glbspVert_t);

					if (glVer == 5)
					{
						glSegs = (glbspSeg_t *)glSegsData;
						numGLSegs = (glSegsLump->size)/sizeof(glbspSeg_t);
						glSubSects = (glbspSubSect_t *)glSubSectData;
						numGLSubSects = (glSubSectLump->size)/sizeof(glbspSubSect_t);
					}
					else if (glVer == 3)
					{
						glSegs = (glbspSeg_t *)(glSegsData+4);
						numGLSegs = (glSegsLump->size-4)/sizeof(glbspSeg_t);
						glSubSects = (glbspSubSect_t *)(glSubSectData+4);
						numGLSubSects = (glSubSectLump->size-4)/sizeof(glbspSubSect_t);
					}
					else
					{
						glbspSegV1_t *v1Segs = (glbspSegV1_t *)glSegsData;
						numGLSegs = (glSegsLump->size)/sizeof(glbspSegV1_t);
						glSegs = (glbspSeg_t *)localPool.Alloc(sizeof(glbspSeg_t)*numGLSegs);
						for (int i = 0; i < numGLSegs; i++)
						{
							const glbspSegV1_t *src = v1Segs+i;
							glbspSeg_t *dst = glSegs+i;
							//take the first 15 bits as the index and shift the last bit up for the new format
							dst->startVert = (src->startVert & 0x7FFF) | ((unsigned int)(src->startVert & 0x8000)<<16);
							dst->endVert = (src->endVert & 0x7FFF) | ((unsigned int)(src->endVert & 0x8000)<<16);
							dst->lineDef = src->lineDef;
							dst->side = src->side;
							dst->partnerSeg = (src->partnerSeg == 0xFFFF) ? 0xFFFFFFFF : src->partnerSeg;
						}
						mapSubSector_t *v1SubSects = (mapSubSector_t *)glSubSectData;
						numGLSubSects = (glSubSectLump->size)/sizeof(mapSubSector_t);
						glSubSects = (glbspSubSect_t *)localPool.Alloc(sizeof(glbspSubSect_t)*numGLSegs);
						for (int i = 0; i < numGLSubSects; i++)
						{
							const mapSubSector_t *src = v1SubSects+i;
							glbspSubSect_t *dst = glSubSects+i;
							dst->segNum = src->segNum;
							dst->firstSeg = src->firstSeg;
						}
					}
				}
			}
		}
	}

	void *pgctx = rapi->rpgCreateContext();

	extraSubSectData_t *extraSS;
	int numExtraSS;
	if (glVerts)
	{
		//we get to take the easy way out
		numExtraSS = numGLSubSects;
		extraSS = Model_DoomWad_TranslateGLSubSectors(lineDefs, numLineDefs, sideDefs, numSideDefs, verts, numVerts,
			glVerts, numGLVerts, glSegs, numGLSegs, glSubSects, numGLSubSects, localPool, rapi);
	}
	else
	{
		numExtraSS = numSubSectors;
		extraSS = Model_DoomWad_CreateConvexSubsectorPolygons(lineDefs, numLineDefs, sideDefs, numSideDefs, verts, numVerts,
						sectors, numSectors, subSectors, numSubSectors, segs, numSegs, nodes, numNodes, localPool, rapi);
	}

	//draw subsectors
	for (int i = 0; i < numExtraSS; i++)
	{
		extraSubSectData_t *ess = extraSS+i;
		mapSector_t *sector = sectors+ess->sectorIndex;

		set_color_for_sector_light(rapi, wl.colorMapLump, sector->lightLevel);

		if (ess->numPoints >= 3)
		{
			noesisTex_t *floorTex = NULL;
			int floorResIndex = mr.flatsHash.GetResourceIndexForId(sector->floorTex);
			if (floorResIndex >= 0)
			{
				floorTex = mr.noeTextures[floorResIndex];
				rapi->rpgSetMaterial(mr.noeMaterials[floorResIndex]->name);
			}
			else
			{
				rapi->rpgSetMaterial("unknown");
			}

			//floor
			rapi->rpgBegin(RPGEO_POLYGON);
			for (int j = 0; j < ess->numPoints; j++)
			{
				polyPoint_t *point = ess->convexPoints+j;
				float v[3] = { float(point->p[0]), float(point->p[1]), sector->floorHeight };
				if (floorTex)
				{
					float uv[2] = { v[0] / float(floorTex->w), -v[1] / float(floorTex->h) };
					rapi->rpgVertUV2f(uv, 0);
				}
				rapi->rpgVertex3f(v);
			}
			rapi->rpgEnd();

			noesisTex_t *ceilTex = NULL;
			int ceilResIndex = mr.flatsHash.GetResourceIndexForId(sector->ceilingTex);
			if (ceilResIndex >= 0)
			{
				ceilTex = mr.noeTextures[ceilResIndex];
				rapi->rpgSetMaterial(mr.noeMaterials[ceilResIndex]->name);
			}
			else
			{
				rapi->rpgSetMaterial("unknown");
			}

			//ceiling
			rapi->rpgBegin(RPGEO_POLYGON);
			for (int j = ess->numPoints-1; j >= 0; j--)
			{
				polyPoint_t *point = ess->convexPoints+j;
				float v[3] = { float(point->p[0]), float(point->p[1]), sector->ceilingHeight };
				if (ceilTex)
				{
					float uv[2] = { v[0] / float(ceilTex->w), -v[1] / float(ceilTex->h) };
					rapi->rpgVertUV2f(uv, 0);
				}
				rapi->rpgVertex3f(v);
			}
			rapi->rpgEnd();
		}
	}

	//draw linedefs
	for (int i = 0; i < numLineDefs; i++)
	{
		mapLineDef_t *lineDef = lineDefs+i;
		mapVert_t *lineV1 = verts+lineDef->startVert;
		mapVert_t *lineV2 = verts+lineDef->endVert;
		mUShort_t *sideDefIndices = &lineDef->rightSideDef;
		for (int j = 0; j < 2; j++)
		{
			int sideDefIndex = sideDefIndices[j];
			if (sideDefIndex == 0xFFFF)
			{
				continue;
			}

			mapSideDef_t *sideDef = sideDefs+sideDefIndex;
			mapSector_t *sector = sectors+sideDef->sectorNum;

			set_color_for_sector_light(rapi, wl.colorMapLump, sector->lightLevel);

			int otherSideIndex = sideDefIndices[(j+1) & 1];
			mapSideDef_t *otherSideDef = (otherSideIndex == 0xFFFF) ? NULL : sideDefs+otherSideIndex;
			mapSector_t *otherSector = (otherSideDef) ? sectors+otherSideDef->sectorNum : NULL;

			const bool backWind = (j == 0);
			//for upper/lower, we want to adjust the winding based on whether there's another sidedef and whether it has a renderable
			//texture. otherwise we either get stuff with the wrong winding (see step on e1m1) or stuff overlapping. (see computer
			//screens on e1m1)
			if (should_render_linedef_area(sideDef->middleTex))
			{
				float floorHeight = sector->floorHeight;
				float ceilingHeight = sector->ceilingHeight;
				if ((lineDef->flags & 0x04) && otherSector)
				{
					//also not sure if this is correct behavior for two-sided lines.
					floorHeight = g_mfn->Math_Max2(sector->floorHeight, otherSector->floorHeight);
					ceilingHeight = g_mfn->Math_Min2(sector->ceilingHeight, otherSector->ceilingHeight);
				}
				const bool backWindMiddle = backWind;
				render_linedef_portion(rapi, mr, sideDef->middleTex, sideDef, sector, otherSector, lineDef, sideDefIndex, lineV1, lineV2,
					floorHeight, ceilingHeight, backWindMiddle, ((lineDef->flags & 0x10) != 0) ? 3 : 0);
			}
			if (otherSector)
			{
				if (should_render_linedef_area(sideDef->upperTex))
				{
					const bool backWindUp = (otherSideDef && should_render_linedef_area(otherSideDef->upperTex)) ? true : backWind;
					render_linedef_portion(rapi, mr, sideDef->upperTex, sideDef, sector, otherSector, lineDef, sideDefIndex, lineV1, lineV2,
						otherSector->ceilingHeight, sector->ceilingHeight, backWindUp, ((lineDef->flags & 0x08) != 0) ? 2 : 0);
				}
				if (should_render_linedef_area(sideDef->lowerTex))
				{
					const bool backWindDown = (otherSideDef && should_render_linedef_area(otherSideDef->lowerTex)) ? true : backWind;
					render_linedef_portion(rapi, mr, sideDef->lowerTex, sideDef, sector, otherSector, lineDef, sideDefIndex, lineV1, lineV2,
						sector->floorHeight, otherSector->floorHeight, backWindDown, ((lineDef->flags & 0x10) != 0) ? 1 : 0);
				}
			}
		}
	}

	rapi->rpgOptimize();
	rapi->rpgSetExData_Materials(mr.noeMatData);

	if (g_opts->weldVerts != 0.0)
	{
		rapi->rpgWeldVerts(float(g_opts->weldVerts), RPG_WELD_FLAG_XY, NULL);
	}

	noesisModel_t *mdl = rapi->rpgConstructModel();
	rapi->rpgDestroyContext(pgctx);

	return mdl;
}

static void Model_DoomWad_LoadTextures(doomMapRes_t &mr, wadLoad_t &wl, noeRAPI_t *rapi)
{
	if (wl.paletteLump.base)
	{
		BYTE *palData = (BYTE *)wl.paletteLump.base + wl.paletteLump.l->ofs;

		//load all the flats
		const int flatWidth = 64;
		const int flatHeight = 64;
		for (int i = 0; i < wl.flatsLumps.Num(); i++)
		{
			memLump_t &fl = wl.flatsLumps[i];
			char endName[8];
			memcpy(endName, fl.l->name, 8);
			memcpy(&endName[3], "END\0\0", 5);
			wadLump_t *flatLump = fl.l+1;
			while (memcmp(flatLump->name, endName, 6) != 0)
			{
				BYTE *flatData = (BYTE *)fl.base + flatLump->ofs;
				char texName[9];
				memcpy(texName, flatLump->name, 8);
				texName[8] = 0;
				BYTE *flatDataColor = apply_color_palette(rapi, flatData, palData, flatWidth, flatHeight);
				noesisTex_t *noeTex = rapi->Noesis_TextureAlloc(texName, flatWidth, flatHeight, flatDataColor, NOESISTEX_RGBA32);
				if (noeTex)
				{
					noeTex->shouldFreeData = true;
					int texIndex = mr.noeTextures.Num();
					mr.noeTextures.Append(noeTex);
					mr.flatsHash.AddResource(flatLump->name, texIndex);

					noesisMaterial_t *noeMat = rapi->Noesis_GetMaterialList(1, true);
					noeMat->name = rapi->Noesis_PooledString(texName);
					noeMat->texIdx = texIndex;
					mr.noeMaterials.Append(noeMat);

					//should match 1 to 1
					assert(mr.noeMaterials.Num() == mr.noeTextures.Num());
				}
				flatLump++;
			}
		}

		//load all the textures
		if (wl.pnamesLump.base)
		{
			DoomResHash patchHash;
			CArrayList<wadPatchData_t> patchDatas;
			for (int i = 0; i < wl.patchesLumps.Num(); i++)
			{
				memLump_t &pl = wl.patchesLumps[i];
				char endName[8];
				memcpy(endName, pl.l->name, 8);
				memcpy(&endName[3], "END\0\0", 5);
				wadLump_t *patchLump = pl.l+1;
				while (memcmp(patchLump->name, endName, 6) != 0)
				{
					BYTE *patchData = (BYTE *)pl.base + patchLump->ofs;
					int resIndex = patchDatas.Num();
					wadPatchData_t newData;
					memset(&newData, 0, sizeof(wadPatchData_t));
					newData.data = patchData;
					newData.size = patchLump->size;
					patchDatas.Append(newData);
					patchHash.AddResource(patchLump->name, resIndex);
					patchLump++;
				}
			}
			BYTE *pnamesHdr = (BYTE *)wl.pnamesLump.base + wl.pnamesLump.l->ofs;
			int numPatchNames = *(int *)pnamesHdr;
			char *patchNames = (char *)(pnamesHdr+sizeof(int));

			for (int i = 0; i < wl.texturesLumps.Num(); i++)
			{
				memLump_t &tl = wl.texturesLumps[i];
				BYTE *hdr = (BYTE *)tl.base + tl.l->ofs;
				int numTextures = *(int *)hdr;
				int *textureOffsets = (int *)(hdr+sizeof(int));
				for (int j = 0; j < numTextures; j++)
				{
					wadTexHdr_t *texHdr = (wadTexHdr_t *)(hdr + textureOffsets[j]);
					BYTE *texData = (BYTE *)rapi->Noesis_UnpooledAlloc(texHdr->width*texHdr->height*4);
					//this way areas that are skipped in the texture will already be alpha-cleared
					memset(texData, 0, texHdr->width*texHdr->height*4);

					for (int k = 0; k < texHdr->patchCount; k++)
					{
						wadTexPatch_t *texPatch = &texHdr->patches[k];
						char *patchName = patchNames + texPatch->patchIndex*8;
						int patchResIndex = patchHash.GetResourceIndexForId(patchName);
						if (patchResIndex < 0)
						{
							rapi->LogOutput("WARNING: Failed to retrieve patch by hash.\n");
						}
						else
						{
							wadPatchData_t &patchData = patchDatas[patchResIndex];
							wadPatchHdr_t *patchHdr = (wadPatchHdr_t *)(patchData.data);
							int *columnOffsets = (int *)(patchData.data + sizeof(wadPatchHdr_t));

							for (int x = 0; x < patchHdr->width; x++)
							{
								int absX = texPatch->originX+x;
								BYTE *colData = patchData.data + columnOffsets[x];
								int dataOfs = 0;
								int ofsY = 0;
								while (dataOfs < patchData.size)
								{
									int ofsOp = colData[dataOfs++];
									if (ofsOp == 0xFF)
									{
										break;
									}
									if (ofsOp != 0)
									{
										ofsY = ofsOp;
									}

									int runLen = colData[dataOfs++];
									dataOfs++; //?
									int runOfs = dataOfs;
									dataOfs++; //?
									dataOfs += runLen;

									int absY = texPatch->originY + ofsY;
									if (absY < 0)
									{
										runLen += absY;
										absY = 0;
									}
									if (absY+runLen > texHdr->height)
									{
										runLen = texHdr->height - absY;
									}

									if (runLen > 0)
									{
										for (int colEntry = 0; colEntry < runLen; colEntry++)
										{
											int y = absY+colEntry;
											if (y < 0 || y >= texHdr->height ||
												absX < 0 || absX >= texHdr->width)
											{
												continue;
											}
											int dstOfs = y*texHdr->width + absX;
											int palIndex = colData[runOfs+colEntry];
											BYTE *palClr = palData + palIndex*3;
											texData[dstOfs*4 + 0] = palClr[0];
											texData[dstOfs*4 + 1] = palClr[1];
											texData[dstOfs*4 + 2] = palClr[2];
											texData[dstOfs*4 + 3] = 255;
										}
										ofsY += runLen;
									}
								}
							}
						}
					}

					char texName[9];
					memcpy(texName, texHdr->name, 8);
					texName[8] = 0;
					noesisTex_t *noeTex = rapi->Noesis_TextureAlloc(texName, texHdr->width, texHdr->height, texData, NOESISTEX_RGBA32);
					if (noeTex)
					{
						noeTex->shouldFreeData = true;
						int texIndex = mr.noeTextures.Num();
						mr.noeTextures.Append(noeTex);
						mr.wallTexHash.AddResource(texHdr->name, texIndex);

						noesisMaterial_t *noeMat = rapi->Noesis_GetMaterialList(1, true);
						noeMat->name = rapi->Noesis_PooledString(texName);
						noeMat->texIdx = texIndex;
						mr.noeMaterials.Append(noeMat);

						//should match 1 to 1
						assert(mr.noeMaterials.Num() == mr.noeTextures.Num());
					}
					else
					{
						rapi->Noesis_UnpooledFree(texData);
					}
				}
			}
		}
	}

	//creating all texture resources once will allow noesis to refcount them for each model, so we don't end up duplicating
	//any texture data between maps.
	mr.noeMatData = rapi->Noesis_GetMatDataFromLists(mr.noeMaterials, mr.noeTextures);
}

static void Model_DoomWad_ParseLumps(BYTE *fileBuffer, int bufferLen, wadLoad_t &wl)
{
	wadHdr_t *hdr = (wadHdr_t *)fileBuffer;
	wadLump_t *lumps = (wadLump_t *)(fileBuffer+hdr->lumpsOfs);

	assert(g_opts);

	for (int i = 0; i < hdr->numLumps; i++)
	{
		wadLump_t *l = lumps+i;
		memLump_t ml;
		memset(&ml, 0, sizeof(ml));
		ml.base = hdr;
		ml.l = l;
		ml.lIdx = i;
		wl.allLumps.Append(ml);
		if (!memcmp(l->name, "COLORMAP", 8))
		{
			wl.colorMapLump = ml;
		}
		else if (!memcmp(l->name, "PLAYPAL", 7))
		{
			wl.paletteLump = ml;
		}
		else if (!memcmp(l->name, "PNAMES", 6))
		{
			wl.pnamesLump = ml;
		}
		else if (!memcmp(l->name, "TEXTURE", 7))
		{
			wl.texturesLumps.Append(ml);
		}
		else if (!memcmp(l->name, "F1_START", 8) || !memcmp(l->name, "F2_START", 8) ||
			!memcmp(l->name, "F3_START", 8) || !memcmp(l->name, "F4_START", 8) || !memcmp(l->name, "F5_START", 8))
		{
			wl.flatsLumps.Append(ml);
		}
		else if (!memcmp(l->name, "P1_START", 8) || !memcmp(l->name, "P2_START", 8) ||
			!memcmp(l->name, "P3_START", 8) || !memcmp(l->name, "P4_START", 8) || !memcmp(l->name, "P5_START", 8))
		{
			wl.patchesLumps.Append(ml);
		}
		else if (!memcmp(l->name, "S_START", 7) || !memcmp(l->name, "S1_START", 8) || !memcmp(l->name, "S2_START", 8))
		{
			wl.spritesLumps.Append(ml);
		}
		else if (wl.allLumps.Num() > 1 && (i+1) < hdr->numLumps && !memcmp((l+1)->name, "THINGS\0\0", 8))
		{
			wl.mapLumps.Append(ml);
		}
		else if (!g_opts->disableGLBSP && !memcmp(l->name, "GL_", 3))
		{
			wl.glLumps.Append(ml);
		}
	}
}

//load it (note that you don't need to worry about validation here, if it was done in the Check function)
noesisModel_t *Model_DoomWad_Load(BYTE *fileBuffer, int bufferLen, int &numMdl, noeRAPI_t *rapi)
{
	wadLoad_t wl;
	memset(&wl, 0, sizeof(wadLoad_t));

	int separateIWADSize = 0;
	BYTE *separateIWADBuffer = NULL;

	//todo - if it's a pwad, prompt to load the iwad here and combine resources.
	//(everything should just work out if we call Model_DoomWad_ParseLumps on the iwad and then the pwad)

	Model_DoomWad_ParseLumps(fileBuffer, bufferLen, wl);

	if (wl.mapLumps.Num() <= 0)
	{
		rapi->LogOutput("ERROR: No maps were found in this wad.\n");
		return NULL;
	}

	BYTE *gwaBuffer = NULL;
	if (!g_opts->disableGLBSP)
	{
		//search for a .gwa
		wchar_t gwaName[MAX_NOESIS_PATH];
		rapi->Noesis_GetExtensionlessNameW(gwaName, rapi->Noesis_GetLastCheckedNameW());
		wcscat_s(gwaName, MAX_NOESIS_PATH, L".gwa");
		int gwaSize = 0;
		gwaBuffer = rapi->Noesis_ReadFileW(gwaName, &gwaSize);
		if (gwaBuffer && Model_DoomWad_Check(gwaBuffer, gwaSize, rapi))
		{
			//parse the gl lumps
			Model_DoomWad_ParseLumps(gwaBuffer, gwaSize, wl);
		}
	}

	doomMapRes_t mr;
	Model_DoomWad_LoadTextures(mr, wl, rapi);

	CArrayList<noesisModel_t *> mapModels;
	for (int i = 0; i < wl.mapLumps.Num(); i++)
	{
		noesisModel_t *mdl = Model_DoomWad_LoadMap(wl.mapLumps[i], wl, mr, rapi);
		if (mdl)
		{
			mapModels.Append(mdl);
		}
	}

	if (gwaBuffer)
	{
		//we can free the buffer now that we're done with the lump data
		rapi->Noesis_UnpooledFree(gwaBuffer);
	}

	if (mapModels.Num() <= 0)
	{
		rapi->LogOutput("ERROR: No maps were loadable in this wad.\n");
		return NULL;
	}

	float mdlAngOfs[3] = {0.0f, 270.0f, 0.0f};
	rapi->SetPreviewAngOfs(mdlAngOfs);

	noesisModel_t *mdls = rapi->Noesis_ModelsFromList(mapModels, numMdl);
	return mdls;
}

//handle -wadcollapseedges
static bool Model_WAD_OptHandlerA(const char *arg, unsigned char *store, int storeSize)
{
	wadOpts_t *lopts = (wadOpts_t *)store;
	assert(storeSize == sizeof(wadOpts_t));
	if (!arg)
	{
		return false;
	}
	lopts->collapseEdges = atof(arg);
	return true;
}

//handle -wadweldverts
static bool Model_WAD_OptHandlerB(const char *arg, unsigned char *store, int storeSize)
{
	wadOpts_t *lopts = (wadOpts_t *)store;
	assert(storeSize == sizeof(wadOpts_t));
	if (!arg)
	{
		return false;
	}
	lopts->weldVerts = atof(arg);
	return true;
}

//handle -wadmincut
static bool Model_WAD_OptHandlerC(const char *arg, unsigned char *store, int storeSize)
{
	wadOpts_t *lopts = (wadOpts_t *)store;
	assert(storeSize == sizeof(wadOpts_t));
	if (!arg)
	{
		return false;
	}
	lopts->minSecCutDist = atof(arg);
	return true;
}

//handle -wadnogl
static bool Model_WAD_OptHandlerD(const char *arg, unsigned char *store, int storeSize)
{
	wadOpts_t *lopts = (wadOpts_t *)store;
	assert(storeSize == sizeof(wadOpts_t));
	lopts->disableGLBSP = true;
	return true;
}

//called by Noesis to init the plugin
bool NPAPI_InitLocal(void)
{
	g_fmtHandle = g_nfn->NPAPI_Register("Doom Wad", ".wad");
	if (g_fmtHandle < 0)
	{
		return false;
	}

	//set the data handlers for this format
	g_nfn->NPAPI_SetTypeHandler_TypeCheck(g_fmtHandle, Model_DoomWad_Check);
	g_nfn->NPAPI_SetTypeHandler_LoadModel(g_fmtHandle, Model_DoomWad_Load);

	//add first parm
	addOptParms_t optParms;
	memset(&optParms, 0, sizeof(optParms));
	optParms.optName = "-wadcollapseedges";
	optParms.optDescr = "collapses map edges with # threshold.";
	optParms.storeSize = sizeof(wadOpts_t);
	optParms.handler = Model_WAD_OptHandlerA;
	optParms.flags |= OPTFLAG_WANTARG;
	g_opts = (wadOpts_t *)g_nfn->NPAPI_AddTypeOption(g_fmtHandle, &optParms);
	assert(g_opts);
	optParms.shareStore = (unsigned char *)g_opts;

	//add subsequent parms
	optParms.optName = "-wadweldverts";
	optParms.optDescr = "welds map verts with # threshold.";
	optParms.handler = Model_WAD_OptHandlerB;
	g_nfn->NPAPI_AddTypeOption(g_fmtHandle, &optParms);

	optParms.optName = "-wadmincut";
	optParms.optDescr = "minimum dist to chop convex subsect poly.";
	optParms.handler = Model_WAD_OptHandlerC;
	g_nfn->NPAPI_AddTypeOption(g_fmtHandle, &optParms);

	optParms.optName = "-wadnogl";
	optParms.optDescr = "disables parsing glbsp lumps and looking for gwa file.";
	optParms.flags &= ~OPTFLAG_WANTARG;
	optParms.handler = Model_WAD_OptHandlerD;
	g_nfn->NPAPI_AddTypeOption(g_fmtHandle, &optParms);

	return true;
}

//called by Noesis before the plugin is freed
void NPAPI_ShutdownLocal(void)
{
	//nothing to do here
}

BOOL APIENTRY DllMain( HMODULE hModule,
                       DWORD  ul_reason_for_call,
                       LPVOID lpReserved
					 )
{
	switch (ul_reason_for_call)
	{
	case DLL_PROCESS_ATTACH:
	case DLL_THREAD_ATTACH:
	case DLL_THREAD_DETACH:
	case DLL_PROCESS_DETACH:
		break;
	}
    return TRUE;
}
